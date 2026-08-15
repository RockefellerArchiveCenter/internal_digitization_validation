from os import getenv
from pathlib import Path
from shutil import rmtree
from unittest.mock import ANY, patch

import pytest
from moto import mock_aws

from src.process_packages import (is_valid_package, main, move_to_dir,
                                  validate_assets, validate_directories)

# TODO move directory creation/removal to fixture

DEFAULT_ARGS = [
    '/spreadsheet/path',
    False,
    'aws:iam:role:internal-digitization-role',
    'rac-dev-digitized-image-upload',
    'restricted',
    'uploaded']


@patch('src.process_packages.to_process')
@patch('src.process_packages.remove_unwanted_files')
@patch('src.process_packages.is_valid_package')
@patch('src.process_packages.rename_files')
@patch('src.process_packages.create_bag')
@patch('src.process_packages.update_bag')
@patch('src.process_packages.create_tarball')
@patch('src.process_packages.upload_package')
@patch('src.process_packages.move_to_dir')
def test_main_with_dir(
        mock_move, mock_upload, mock_tarball, mock_update_bag, mock_create_bag,
        mock_rename, mock_is_valid, mock_unwanted, mock_data):
    current_dir = '/volumes/data/Digitization/123456'
    refid = '1a2b3c4d5e6f7h8i9j10k'
    mock_data.return_value = [(current_dir, refid)]
    mock_is_valid.return_value = True
    mock_rename.return_value = f'/volumes/data/Digitization/{refid}'
    mock_tarball.return_value = f'/volumes/data/Digitization/{refid}.tar.gz'
    Path(current_dir).mkdir(parents=True)

    main(*DEFAULT_ARGS)

    mock_data.assert_called_once_with('/spreadsheet/path')
    mock_unwanted.assert_called_once_with(Path(current_dir))
    mock_is_valid.assert_called_once_with(Path(current_dir))
    mock_rename.assert_called_once_with(Path(current_dir), refid)
    mock_create_bag.assert_called_once_with(f'/volumes/data/Digitization/{refid}')
    mock_update_bag.assert_not_called()
    mock_tarball.assert_called_once_with(f'/volumes/data/Digitization/{refid}')
    mock_upload.assert_called_once_with(f'/volumes/data/Digitization/{refid}.tar.gz', ANY)
    mock_move.assert_called_once_with(f'/volumes/data/Digitization/{refid}.tar.gz', 'uploaded')
    rmtree(current_dir)


@patch('src.process_packages.to_process')
@patch('src.process_packages.remove_unwanted_files')
@patch('src.process_packages.is_valid_package')
@patch('src.process_packages.rename_files')
@patch('src.process_packages.create_bag')
@patch('src.process_packages.update_bag')
@patch('src.process_packages.create_tarball')
@patch('src.process_packages.upload_package')
@patch('src.process_packages.move_to_dir')
def test_main_with_bag(
        mock_move, mock_upload, mock_tarball, mock_update_bag, mock_create_bag,
        mock_rename, mock_is_valid, mock_unwanted, mock_data):
    refid = '1a2b3c4d5e6f7h8i9j10k'
    current_dir = f'/volumes/data/Digitization/Backlog Project/{refid}'
    mock_data.return_value = [(current_dir, refid)]
    mock_is_valid.return_value = True
    mock_rename.return_value = current_dir
    mock_tarball.return_value = f'/volumes/data/Digitization/Backlog Project/{refid}.tar.gz'
    Path(current_dir).mkdir(parents=True)

    main(*DEFAULT_ARGS)

    mock_data.assert_called_once_with('/spreadsheet/path')
    mock_unwanted.assert_called_once_with(Path(current_dir))
    mock_is_valid.assert_called_once_with(Path(current_dir, 'data'))
    mock_rename.assert_not_called()
    mock_create_bag.assert_not_called()
    mock_update_bag.assert_called_once_with(current_dir)
    mock_tarball.assert_called_once_with(Path(current_dir))
    mock_upload.assert_called_once_with(f'/volumes/data/Digitization/{refid}.tar.gz', ANY)
    mock_move.assert_called_once_with(f'/volumes/data/Digitization/{refid}.tar.gz', getenv('UPLOADED_DIR'))
    rmtree(current_dir)


@patch('src.process_packages.to_process')
@patch('src.process_packages.remove_unwanted_files')
@patch('src.process_packages.is_valid_package')
@patch('src.process_packages.rename_files')
@patch('src.process_packages.create_bag')
@patch('src.process_packages.update_bag')
@patch('src.process_packages.create_tarball')
@patch('src.process_packages.upload_package')
@patch('src.process_packages.move_to_dir')
def test_main_with_restricted(
        mock_move, mock_upload, mock_tarball, mock_update_bag, mock_create_bag,
        mock_rename, mock_is_valid, mock_unwanted, mock_data):
    current_dir = 'volumes/data/Digitization/123456'
    refid = '1a2b3c4d5e6f7h8i9j10k'
    mock_data.return_value = [(current_dir, refid)]
    mock_is_valid.return_value = True
    mock_rename.return_value = f'/volumes/data/Digitization/{refid}'
    mock_tarball.return_value = f'/volumes/data/Digitization/{refid}.tar.gz'
    Path(current_dir).mkdir(parents=True)
    updated_args = DEFAULT_ARGS
    updated_args[1] = True

    main(*updated_args)

    mock_data.assert_called_once_with('/spreadsheet/path')
    mock_unwanted.assert_called_once_with(Path(current_dir))
    mock_is_valid.assert_called_once_with(Path(current_dir))
    mock_rename.assert_called_once_with(Path(current_dir), refid)
    mock_create_bag.assert_not_called()
    mock_update_bag.assert_not_called()
    mock_tarball.assert_not_called()
    mock_upload.assert_not_called()
    mock_move.assert_called_once_with(f'/volumes/data/Digitization/{refid}', getenv('RESTRICTED_DIR'))
    rmtree(current_dir)


def test_move_to_dir_with_dir():
    current_dir = Path('this/is/the/current')
    target_dir = 'target'
    current_dir.mkdir(parents=True)

    move_to_dir(current_dir, target_dir)

    assert Path(target_dir, 'current').is_dir()
    assert not current_dir.exists()
    rmtree(target_dir)


def test_move_to_dir_with_file():
    current_file = Path('this/is/the/current.tar.gz')
    with open(current_file, 'w') as tf:
        tf.write("test")
    target_dir = 'target'

    move_to_dir(current_file, target_dir)

    assert Path(target_dir, 'current.tar.gz').is_file()
    assert not current_file.exists()
    rmtree(target_dir)


@patch('src.process_packages.validate_assets')
@patch('src.process_packages.validate_file_formats')
@patch('src.process_packages.validate_ocr')
def test_is_valid_package(mock_ocr, mock_format, mock_assets):
    dir_path = Path('/path/to/package')

    output = is_valid_package(dir_path)

    assert output
    mock_assets.assert_called_once_with(dir_path, dir_path.stem)
    mock_format.assert_called_once_with(dir_path)
    mock_ocr.assert_called_once_with(dir_path, dir_path.stem)


@patch('src.process_packages.validate_assets')
@patch('src.process_packages.validate_file_formats')
@patch('src.process_packages.validate_ocr')
def test_is_valid_package_with_exception(mock_ocr, mock_format, mock_assets):
    mock_assets.return_value = Exception
    dir_path = Path('/path/to/package')

    output = is_valid_package(dir_path)

    assert not output
    mock_assets.assert_called_once_with(dir_path, dir_path.stem)
    mock_format.assert_not_called()
    mock_ocr.assert_not_called()


@patch('src.process_packages.validate_directories')
@patch('src.process_packages.validate_file_counts')
@patch('src.process_packages.validate_file_names')
def test_validate_assets(mock_names, mock_counts, mock_dirs):
    bag_path = Path('/Path/to/bag')
    current_dir = 'current_dir'

    validate_assets(bag_path, current_dir)

    mock_dirs.assert_called_once_with(bag_path)
    mock_counts.assert_called_once_with(bag_path, current_dir)
    mock_names.assert_called_once_with(bag_path)


@patch('src.process_packages.validate_directories')
@patch('src.process_packages.validate_file_counts')
@patch('src.process_packages.validate_file_names')
def test_validate_assets_with_exception(mock_names, mock_counts, mock_dirs):
    mock_dirs.return_value = Exception()
    bag_path = Path('/Path/to/bag')
    current_dir = 'current_dir'

    validate_assets(bag_path, current_dir)

    mock_dirs.assert_called_once_with(bag_path)
    mock_counts.assert_not_called()
    mock_names.assert_not_called()


def test_validate_directories():
    dir_path = Path('/current/path')
    dir_path.mkdir(parents=True)
    for dir in ['master', 'master_edited', 'service_edited']:
        (dir_path / dir).mkdir()

    validate_directories(dir_path)  # Happy path

    rmtree(dir_path / 'master_edited')

    with pytest.raises(FileNotFoundError) as err:
        validate_directories(dir_path)  # With exception

    assert 'master_edited' in str(err.exception)
    rmtree(dir_path)


def test_validate_file_counts():
    pass


def test_validate_file_names():
    pass


def test_validate_ocr():
    pass


def test_validate_file_formats():
    pass


def test_remove_unwanted_files():
    pass


def test_rename_files():
    pass


def test_create_tarball():
    pass


@mock_aws
def test_upload_package():
    pass
