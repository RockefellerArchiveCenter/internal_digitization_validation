import random
from pathlib import Path
from shutil import copyfile, copytree, rmtree
from unittest.mock import patch

import pytest

from src.process_packages import (create_tarball, is_valid_package, main,
                                  move_to_dir, remove_unwanted_files,
                                  rename_files, validate_assets,
                                  validate_directories, validate_file_counts,
                                  validate_file_formats, validate_file_names,
                                  validate_ocr)

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
    mock_upload.assert_called_once_with(
        f'/volumes/data/Digitization/{refid}.tar.gz',
        'rac-dev-digitized-image-upload',
        'aws:iam:role:internal-digitization-role')
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
    mock_upload.assert_called_once_with(
        f'/volumes/data/Digitization/Backlog Project/{refid}.tar.gz',
        'rac-dev-digitized-image-upload',
        'aws:iam:role:internal-digitization-role')
    mock_move.assert_called_once_with(f'/volumes/data/Digitization/Backlog Project/{refid}.tar.gz', 'uploaded')
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
    current_dir = '/volumes/data/Digitization/123456'
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
    mock_assets.side_effect = Exception()
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
    mock_dirs.side_effect = Exception("foo")
    bag_path = Path('/Path/to/bag')
    current_dir = 'current_dir'

    with pytest.raises(Exception) as err:
        validate_assets(bag_path, current_dir)
    assert str(err.value) == 'Package structure is invalid: foo'

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

    assert 'master_edited' in str(err.value)
    rmtree(dir_path)


def test_validate_file_counts_master(file_fixture):
    msg = '2 files found in master_edited directory but only 1 in master directory'
    files = list(TMP_PATH.glob('master/*'))
    random.choice(files).unlink()

    with pytest.raises(Exception) as err:
        validate_file_counts(TMP_PATH, BAG_REFID)
    assert str(err.value) == msg


def test_validate_file_counts_master_edited(file_fixture):
    msg = 'PDF has 2 pages but found 1 files in master_edited directory'
    files = list(TMP_PATH.glob('master_edited/*'))
    random.choice(files).unlink()

    with pytest.raises(Exception) as err:
        validate_file_counts(TMP_PATH, BAG_REFID)
    assert str(err.value) == msg


def test_validate_file_names_with_space(file_fixture):
    file = random.choice(list((TMP_PATH / 'master').iterdir()))
    new_name = file.name.replace("_", " _")
    file.rename(TMP_PATH / 'master' / new_name)

    with pytest.raises(Exception) as err:
        validate_file_names(TMP_PATH)
    assert "contains space" in str(err.value)
    assert new_name in str(err.value)


def test_validate_ocr(file_fixture):
    validate_ocr(TMP_PATH, BAG_REFID)

    # Assert PDFs without OCR raise error.
    copyfile(
        Path("tests", "fixtures", "non-text-searchable.pdf"),
        TMP_PATH / 'service_edited' / f'{BAG_REFID}.pdf')

    with pytest.raises(Exception) as err:
        validate_ocr(TMP_PATH, BAG_REFID)
    assert BAG_REFID in str(err.value)


def test_validate_file_formats(file_fixture):
    """Asserts file formats are validated as expected."""
    validate_file_formats(TMP_PATH)


@patch('src.process_packages.validate_file_characteristics')
def test_validate_file_formats_with_error(mock_characteristics, file_fixture):
    error_string = 'This is an error!'
    mock_characteristics.side_effect = AssertionError(error_string)
    with pytest.raises(Exception) as err:
        validate_file_formats(TMP_PATH)
    assert error_string in (str(err.value))

    error_string = 'This is a different error!'
    mock_characteristics.side_effect = Exception(error_string)
    with pytest.raises(Exception) as err:
        validate_file_formats(TMP_PATH)
    assert error_string in (str(err.value))


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
