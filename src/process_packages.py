#!/usr/bin/env python3

import logging
import tarfile
from os import getenv
from pathlib import Path
from shutil import copytree, rmtree

import bagit
import boto3
import pandas
from aws_assume_role_lib import assume_role

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s::%(funcName)s::%(lineno)s %(message)s')
logging.getLogger("bagit").setLevel(logging.ERROR)


def main(spreadsheet_path, restricted_batch, aws_role_arn, aws_bucket_name, restricted_dir, uploaded_dir, root_dir):
    """Main method which calls all other submethods."""
    for current_dir, refid in to_process(Path(root_dir, spreadsheet_path)):
        logging.info(f"Processing package {refid} located at {current_dir}")
        package_root_path = Path(root_dir, current_dir)
        uploaded_path = Path(root_dir, uploaded_dir)
        restricted_path = Path(root_dir, restricted_dir)
        package_type = 'dir'
        if 'Backlog Project' in current_dir:
            package_type = 'bag'
        assert package_root_path.is_dir(), f"Package does not exist at {package_root_path}"

        remove_unwanted_files(package_root_path)
        logging.info(f"Unwanted files removed from {refid}")

        if package_type == 'dir':
            renamed_path = rename_files(package_root_path, refid)
            logging.info(f"Files in package {refid} renamed")

        if restricted_batch:
            move_to_dir(renamed_path, restricted_path)
            logging.info(f"Package {refid} is restricted, moving to {restricted_path}")
        else:
            if package_type == 'dir':
                create_bag(str(renamed_path))
                logging.info(f"Bag created for package {refid}")
                tarball_path = create_tarball(renamed_path)
                logging.info(f"Tarball created at {tarball_path}")
            else:
                update_bag(str(package_root_path))
                logging.info(f"Bag created for package {refid}")
                tarball_path = create_tarball(package_root_path)
                logging.info(f"Tarball created at {tarball_path}")
            upload_package(tarball_path, aws_bucket_name, aws_role_arn)
            logging.info(f"Package {tarball_path} uploaded to {aws_bucket_name}")
            move_to_dir(tarball_path, uploaded_path)
            logging.info(f"Package {tarball_path} moved to {uploaded_path}")


def to_process(spreadsheet_path):
    """Iterator to return data from spreadsheet.

    Args:
        spreadsheet_path (str): Location of XSLX spreadsheet to parse.

    Returns:
        Iterator of current_dir, refid
    """
    df = pandas.read_excel(spreadsheet_path, header=0)
    for index, row in df.iterrows():
        refid = str(row['refid']).strip()
        current_dir = str(row['current_path']).strip()
        yield current_dir, refid


def move_to_dir(current_path, target_dir):
    """Move digitized directory or file to new target.

    Args:
        current_path (pathlib.Path): current path of digitized object
        target_dir (str): path for new digitized object
    """
    dest_path = Path(target_dir, current_path.stem)
    Path(target_dir).mkdir(exist_ok=True, parents=True)
    if current_path.is_dir():
        copytree(current_path, dest_path)
        rmtree(current_path)
    else:
        current_path.rename(Path(target_dir, current_path.name))


def remove_unwanted_files(dir_path):
    """Removes unwanted files from directory.

    Args:
        dir_path (pathlib.Path): directory from which files should be removed.
    """
    for fp in dir_path.rglob("*"):
        if fp.name in ["Thumbs.db", ".DS_Store"]:
            fp.unlink()


def rename_files(dir_path, refid):
    """Renames files associated with a digital object to match RAC specifications.

    Args:
        dir_path (pathlib.Path): path of digital object to rename
        refid (str): ref ID for digital object, used as basis for file renaming
    """
    for fp in dir_path.rglob("*"):
        if fp.is_file():
            iterator = str(int(fp.stem.split("_")[-1])).zfill(4) if len(fp.stem.split("_")) > 1 else None
            if iterator:
                new_name = fp.with_name(f"{refid}_{iterator}{fp.suffix}")
            else:
                new_name = fp.with_name(f"{refid}{fp.suffix}")
            fp.rename(new_name)
    copytree(dir_path, dir_path.with_name(refid))
    rmtree(dir_path)
    return (dir_path.with_name(refid))


def create_bag(dir):
    """Creates BagIt bag from directory.

    Args:
        dir (str): Path to directory to be bagged
    """
    bagit.make_bag(dir)


def update_bag(dir):
    """Updates existing BagIt bag.

    Args (str): Directory containing bag to be updated
    """
    bag = bagit.Bag(dir)
    bag.save(manifests=True)


def create_tarball(dir_path):
    """Create tarball from bagged path.

    Args:
        dir_path (pathlib.Path): path of digital object to tarball

    Returns:
        tar_path (pathlib.Path): path to tarball
    """
    tar_path = dir_path.with_name(f"{dir_path.name}.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(dir_path, arcname=dir_path.name)
    rmtree(dir_path)
    return tar_path


def upload_package(tarball_path, aws_bucket_name, aws_role_arn):
    """Uploads package to S3 bucket.

    Args:
        tarball_path (pathlib.Path): Path of file to upload.
        aws_bucket_name (str): name of S3 bucket to upload files to
        aws_role_arn (str): Name of AWS role to assume in session
    """
    session = boto3.Session()
    assumed_role_session = assume_role(session, aws_role_arn)
    s3_client = assumed_role_session.client('s3', region_name='us-east-1')
    s3_client.upload_file(str(tarball_path), aws_bucket_name, tarball_path.name)


if __name__ == '__main__':
    spreadsheet_path = getenv('SPREADSHEET_PATH')
    restricted_batch = getenv('RESTRICTED_BATCH')
    aws_role_arn = getenv('AWS_ROLE_ARN')
    aws_bucket_name = getenv('AWS_BUCKET_NAME')
    restricted_dir = getenv('RESTRICTED_DIR')
    uploaded_dir = getenv('UPLOADED_DIR')
    root_dir = getenv('ROOT_DIR')
    main(
        spreadsheet_path,
        restricted_batch,
        aws_role_arn,
        aws_bucket_name,
        restricted_dir,
        uploaded_dir,
        root_dir)
