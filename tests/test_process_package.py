from pathlib import Path
from shutil import copytree, rmtree
from unittest.mock import patch

import pytest

from src.process_packages import (create_tarball, main, move_to_dir,
                                  remove_unwanted_files, rename_files)

DEFAULT_ARGS = [
    '/spreadsheet/path',
    False,
    'aws:iam:role:internal-digitization-role',
    'rac-dev-digitized-image-upload',
    'restricted',
    'uploaded',
    '/local_storage']

BAG_REFID = "b90862f3baceaae3b7418c78f9d50d52"
FIXTURE_PATH = Path("tests", "fixtures", BAG_REFID)
TMP_PATH = Path("tmp", BAG_REFID)


@pytest.fixture()
def file_fixture():
    """Fixture to create and tear down dir before and after a test is run"""
    copytree(FIXTURE_PATH, TMP_PATH)

    yield  # this is where the testing happens

    if TMP_PATH.is_dir():
        rmtree(TMP_PATH)


@patch('src.process_packages.to_process')
@patch('src.process_packages.remove_unwanted_files')
@patch('src.process_packages.rename_files')
@patch('src.process_packages.create_bag')
@patch('src.process_packages.update_bag')
@patch('src.process_packages.create_tarball')
@patch('src.process_packages.upload_package')
@patch('src.process_packages.move_to_dir')
def test_main_with_dir(
        mock_move, mock_upload, mock_tarball, mock_update_bag, mock_create_bag,
        mock_rename, mock_unwanted, mock_data):
    current_dir = '/volumes/data/Digitization/123456'
    refid = '1a2b3c4d5e6f7h8i9j10k'
    mock_data.return_value = [(current_dir, refid)]
    mock_rename.return_value = f'/volumes/data/Digitization/{refid}'
    mock_tarball.return_value = f'/volumes/data/Digitization/{refid}.tar.gz'
    Path(current_dir).mkdir(parents=True)

    main(*DEFAULT_ARGS)

    mock_data.assert_called_once_with('/spreadsheet/path')
    mock_unwanted.assert_called_once_with(Path(current_dir))
    mock_rename.assert_called_once_with(Path(current_dir), refid)
    mock_create_bag.assert_called_once_with(f'/volumes/data/Digitization/{refid}')
    mock_update_bag.assert_not_called()
    mock_tarball.assert_called_once_with(f'/volumes/data/Digitization/{refid}')
    mock_upload.assert_called_once_with(
        f'/volumes/data/Digitization/{refid}.tar.gz',
        'rac-dev-digitized-image-upload',
        'aws:iam:role:internal-digitization-role')
    mock_move.assert_called_once_with(f'/volumes/data/Digitization/{refid}.tar.gz', 'uploaded')
    rmtree(current_dir)


@patch('src.process_packages.to_process')
@patch('src.process_packages.remove_unwanted_files')
@patch('src.process_packages.rename_files')
@patch('src.process_packages.create_bag')
@patch('src.process_packages.update_bag')
@patch('src.process_packages.create_tarball')
@patch('src.process_packages.upload_package')
@patch('src.process_packages.move_to_dir')
def test_main_with_bag(
        mock_move, mock_upload, mock_tarball, mock_update_bag, mock_create_bag,
        mock_rename, mock_unwanted, mock_data):
    refid = '1a2b3c4d5e6f7h8i9j10k'
    current_dir = f'/volumes/data/Digitization/Backlog Project/{refid}'
    mock_data.return_value = [(current_dir, refid)]
    mock_rename.return_value = current_dir
    mock_tarball.return_value = f'/volumes/data/Digitization/Backlog Project/{refid}.tar.gz'
    Path(current_dir).mkdir(parents=True)

    main(*DEFAULT_ARGS)

    mock_data.assert_called_once_with('/spreadsheet/path')
    mock_unwanted.assert_called_once_with(Path(current_dir))
    mock_rename.assert_not_called()
    mock_create_bag.assert_not_called()
    mock_update_bag.assert_called_once_with(current_dir)
    mock_tarball.assert_called_once_with(Path(current_dir))
    mock_upload.assert_called_once_with(
        f'/volumes/data/Digitization/Backlog Project/{refid}.tar.gz',
        'rac-dev-digitized-image-upload',
        'aws:iam:role:internal-digitization-role')
    mock_move.assert_called_once_with(f'/volumes/data/Digitization/Backlog Project/{refid}.tar.gz', 'uploaded')
    rmtree(current_dir)


@patch('src.process_packages.to_process')
@patch('src.process_packages.remove_unwanted_files')
@patch('src.process_packages.rename_files')
@patch('src.process_packages.create_bag')
@patch('src.process_packages.update_bag')
@patch('src.process_packages.create_tarball')
@patch('src.process_packages.upload_package')
@patch('src.process_packages.move_to_dir')
def test_main_with_restricted(
        mock_move, mock_upload, mock_tarball, mock_update_bag, mock_create_bag,
        mock_rename, mock_unwanted, mock_data):
    current_dir = '/volumes/data/Digitization/123456'
    refid = '1a2b3c4d5e6f7h8i9j10k'
    mock_data.return_value = [(current_dir, refid)]
    mock_rename.return_value = f'/volumes/data/Digitization/{refid}'
    mock_tarball.return_value = f'/volumes/data/Digitization/{refid}.tar.gz'
    Path(current_dir).mkdir(parents=True)
    updated_args = DEFAULT_ARGS
    updated_args[1] = True

    main(*updated_args)

    mock_data.assert_called_once_with('/spreadsheet/path')
    mock_unwanted.assert_called_once_with(Path(current_dir))
    mock_rename.assert_called_once_with(Path(current_dir), refid)
    mock_create_bag.assert_not_called()
    mock_update_bag.assert_not_called()
    mock_tarball.assert_not_called()
    mock_upload.assert_not_called()
    mock_move.assert_called_once_with(f'/volumes/data/Digitization/{refid}', 'restricted')
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


def test_remove_unwanted_files(file_fixture):
    initial_file_count = len(list(TMP_PATH.rglob('*')))

    for dir in ['master', 'service_edited']:
        for filename in ['.DS_Store', 'Thumbs.db']:
            with open(TMP_PATH / dir / filename, 'w') as fp:
                fp.write('test')

    remove_unwanted_files(TMP_PATH)

    processed_file_count = len(list(TMP_PATH.rglob('*')))
    assert initial_file_count == processed_file_count


def test_rename_files(file_fixture):
    new_refid = 'new_refid'

    rename_files(TMP_PATH, new_refid)

    assert Path("tmp", new_refid).is_dir()
    assert Path("tmp", new_refid, 'master', f'{new_refid}_0001.tif').is_file()
    assert Path("tmp", new_refid, 'service_edited', f'{new_refid}.pdf').is_file()

    rmtree(Path("tmp", new_refid))


def test_create_tarball():
    current_dir = Path("/current/dir")
    current_dir.mkdir(parents=True)
    create_tarball(current_dir)
    assert Path('/current/dir.tar.gz').is_file()
    assert not current_dir.exists()
