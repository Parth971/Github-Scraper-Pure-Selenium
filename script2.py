import logging
import os
import pathlib
import shutil
import zipfile
from logging.handlers import RotatingFileHandler

BASE_DIR = pathlib.Path(__file__).parent.resolve()

log_file = BASE_DIR / 'outputs/unzip.log'

root_logger = logging.getLogger(__name__)
root_logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

rotating_file_log = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=1)
rotating_file_log.setFormatter(formatter)

console_log = logging.StreamHandler()
console_log.setLevel(logging.INFO)
console_log.setFormatter(formatter)

root_logger.addHandler(rotating_file_log)
root_logger.addHandler(console_log)


class Utils:
    @staticmethod
    def save_failed_link(unzipped_file_name):
        failed_link_file_path = BASE_DIR / 'outputs/unzip_failed_link.txt'
        with open(failed_link_file_path, 'a') as file:
            file.write(f'{unzipped_file_name}\n')


class UnZip:
    def __init__(self, zips_input_path):
        self.zips_path = zips_input_path
        self.already_unzipped_files, self.files = self.get_all_zips()
        self.clean_up()

    def run(self):
        root_logger.info('Starting Unzipping.')
        root_logger.info(f'Found {len(self.files)} zips to be unzipped.')
        for file_name in self.files:
            root_logger.debug(f'{file_name} is unzipping...')

            try:
                with zipfile.ZipFile(self.zips_path / str(file_name), 'r') as zip_ref:
                    unzipped_file_name = zip_ref.infolist()[0].filename[:-1]
                    zip_ref.extractall(self.zips_path)
                    UnZip.rename_file(self.zips_path, unzipped_file_name, file_name)
            except zipfile.BadZipFile:
                message = f'File not unzipped properly. {file_name} is Corrupted file!'
                root_logger.error(f"File unzip failed. Error: {message}")
                Utils.save_failed_link(file_name)

    def get_all_zips(self):
        all_zip_files = set()
        dir_list = os.listdir(self.zips_path)
        for file_name in dir_list:
            if not os.path.isdir(self.zips_path / file_name) and str(file_name)[-4:] == '.zip':
                all_zip_files.add(file_name)

        root_logger.debug(f'\n\nTotal zips are {len(all_zip_files)}')

        file_path = BASE_DIR / 'outputs/unzipped_repositories.txt'

        if not os.path.exists(file_path):
            return list(), all_zip_files

        already_unzipped_files = set()
        with open(file_path, 'r') as file:
            for file_name in file.readlines():
                already_unzipped_files.add(file_name.strip())

        return already_unzipped_files, all_zip_files - already_unzipped_files

    @classmethod
    def rename_file(cls, base_path, old_file_name, new_file_name):
        old_name = base_path / old_file_name
        new_name = base_path / new_file_name[:-4]
        os.rename(old_name, new_name)
        message = f'Unzipped successfully: {new_file_name[:-4]}'
        root_logger.info(message)
        UnZip.unzipped_repositories(name=new_file_name)

    @classmethod
    def unzipped_repositories(cls, name):
        unzipped_repositories_file_path = BASE_DIR / 'outputs/unzipped_repositories.txt'
        with open(unzipped_repositories_file_path, 'a') as file:
            file.write(name + '\n')

    def clean_up(self):
        message = 'Started Cleanup.'
        root_logger.info(message)

        folder_path = self.zips_path
        dir_list = os.listdir(folder_path)
        for file_name in dir_list:
            if os.path.isdir(folder_path / str(file_name)) and f'{file_name}.zip' not in self.already_unzipped_files:
                message = f'Removing file : {file_name}'
                root_logger.info(message)
                shutil.rmtree(folder_path / f'{file_name}')


if __name__ == '__main__':
    zips_path = BASE_DIR / 'RepoDownloads'
    UnZip(zips_input_path=zips_path).run()





