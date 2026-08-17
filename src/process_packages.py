#!/usr/bin/env python3

import tarfile
from os import getenv
from pathlib import Path
from shutil import copytree, rmtree

import bagit
import boto3
import pandas
import pymupdf
from PIL import Image


def main(spreadsheet_path, restricted_batch, aws_role_name, aws_bucket_name, restricted_dir, uploaded_dir, root_dir):
    """Main method which calls all other submethods."""
    for current_dir, refid in to_process(spreadsheet_path):
        package_root_path = Path(root_dir, current_dir)
        package_payload_path = Path(root_dir, current_dir)
        package_type = 'dir'
        if 'Backlog Project' in current_dir:
            package_payload_path = Path(root_dir, current_dir, 'data')
            package_type = 'bag'
        assert package_root_path.is_dir(), f"Package does not exist at {package_root_path}"

        remove_unwanted_files(package_root_path)

        if is_valid_package(package_payload_path):
            renamed_path = package_root_path
            if package_type == 'dir':
                renamed_path = rename_files(package_root_path, refid)

            if restricted_batch:
                move_to_dir(renamed_path, restricted_dir)
            else:
                if package_type == 'dir':
                    create_bag(str(renamed_path))
                    tarball_path = create_tarball(renamed_path)
                else:
                    update_bag(str(package_root_path))
                    tarball_path = create_tarball(package_root_path)
                upload_package(tarball_path, aws_bucket_name, aws_role_name)
                move_to_dir(tarball_path, uploaded_dir)


def to_process(spreadsheet_path):
    """Iterator to return data from spreadsheet.

    Args:
        spreadsheet_path (str): Location of XSLX spreadsheet to parse.

    Returns:
        Iterator of current_dir, refid
    """
    df = pandas.read_excel(spreadsheet_path, header=0)
    for index, row in df.iterrows():
        refid = row['refid'].strip()
        current_dir = row['current_path'].strip()
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


def is_valid_package(dir_path):
    """Validates package structure and assets.

    Args:
        dir_path (pathlib.Path): path of digitized object to validate.
    """
    try:
        validate_assets(dir_path, dir_path.stem)
        validate_file_formats(dir_path)
        validate_ocr(dir_path, dir_path.stem)
        return True
    except Exception as e:
        print(e)
        return False


def validate_directories(dir_path):
    """Checks for the presence of expected directories.

    Args:
        dir_path (pathlib.Path): path of digitized assets.

    Raises:
        FileNotFoundError if not all directories are present.
    """
    for dir in ['master', 'master_edited', 'service_edited']:
        if not (dir_path / dir).is_dir():
            raise FileNotFoundError(f"Expected directory {dir} is missing")


def validate_file_counts(dir_path, current_dir):
    """Asserts correct number of files is present in each directory.

    Args:
        dir_path (pathlib.Path): path of digitized assets.
        current_dir (str): Name of the top-level directory containing assets.
    """
    with pymupdf.open(dir_path / 'service_edited' / f'{current_dir}.pdf', filetype='pdf') as document:
        pdf_page_count = document.page_count
    master_file_count = len(list((dir_path / 'master').glob(f'{current_dir}*.tif')))
    master_edited_file_count = len(
        list((dir_path / 'master_edited').glob(f'{current_dir}*.tif')))
    if pdf_page_count != master_edited_file_count:
        raise Exception(
            f"PDF has {pdf_page_count} pages but found {master_edited_file_count} files in master_edited directory")
    if master_file_count < master_edited_file_count:
        raise Exception(
            f"{master_edited_file_count} files found in master_edited directory but only {master_file_count} in master directory")


def validate_file_names(dir_path):
    """Ensures file names are valid.

    Args:
        bag_path (pathlib.Path): path of bagit Bag containing assets.
    """
    for dir in ['master', 'master_edited', 'service_edited']:
        for fp in (dir_path / dir).iterdir():
            if " " in fp.name:
                raise Exception(f"File name {str(fp)} contains space.")


def validate_ocr(dir_path, current_dir):
    """Ensures there is an OCR layer for each page of the PDF.

    Args:
        bag_path (pathlib.Path): path of bagit Bag containing assets.
        current_dir (str): Name of the top-level directory containing assets.
    """
    with pymupdf.open(dir_path / 'service_edited' / f'{current_dir}.pdf', filetype='pdf') as document:
        for page in document:
            if page.get_text("text"):
                return True
    raise Exception(f'No OCR detected in package {current_dir}')


def validate_assets(bag_path, current_dir):
    """Ensures that all expected directories and files are present.

    Args:
        bag_path (pathlib.Path): path of directory containing assets.
        current_dir (str): Name of the top-level directory containing assets.

    Raises:
        AssetValidationError if files delivered do not match expected files.
    """
    try:
        validate_directories(bag_path)
        validate_file_counts(bag_path, current_dir)
        validate_file_names(bag_path)
    except Exception as e:
        raise Exception(
            f"Package structure is invalid: {e}") from e


def validate_file_characteristics(image_path):
    with Image.open(image_path) as image:
        image.load()  # Ensures TIFF is valid
        assert image.mode in ["L", "RGB"], f"Image format should be RGB or L, got {image.mode}."
        resolution = image.info.get('dpi', image.info.get('resolution'))
        assert resolution, "Image does not have embedded resolution information."
        assert resolution[0] >= 400 and resolution[1] >= 400, f"Image resolution should be at least 400dpi, got {image.info['dpi']}"


def validate_file_formats(bag_path):
    """Ensures that files pass format validation rules.

    Args:
        bag_path (pathlib.Path): path of bagit Bag containing assets.
    """
    for dir in ['master', 'master_edited']:
        for fp in (bag_path / dir).glob('*.tif'):
            try:
                validate_file_characteristics(fp)
            except AssertionError as e:
                raise Exception(f"TIFF file does not meet specs: {e}")
            except Exception as e:
                raise Exception(f"Invalid TIFF file {str(fp)}: {e}")


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


def upload_package(tarball_path, aws_bucket_name, aws_role_name):
    """Uploads package to S3 bucket.

    Args:
        tarball_path (pathlib.Path): Path of file to upload.
        client (boto3.client): S3 client
        aws_bucket_name (str): name of S3 bucket to upload files to
    """
    aws_session = boto3.Session(profile_name=aws_role_name)
    s3_client = aws_session.client('s3')
    s3_client.upload_file(str(tarball_path), aws_bucket_name, tarball_path.name)


if __name__ == '__main__':
    spreadsheet_path = getenv('SPREADSHEET_PATH')
    restricted_batch = getenv('RESTRICTED_BATCH')
    aws_role_name = getenv('AWS_ROLE_NAME')
    aws_bucket_name = getenv('AWS_BUCKET_NAME')
    restricted_dir = getenv('RESTRICTED_DIR')
    uploaded_dir = getenv('UPLOADED_DIR')
    root_dir = getenv('ROOT_DIR')
    main(
        spreadsheet_path,
        restricted_batch,
        aws_role_name,
        aws_bucket_name,
        restricted_dir,
        uploaded_dir,
        root_dir)
