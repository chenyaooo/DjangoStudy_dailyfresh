from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):
    """自定义文件存储类"""

    def __init__(self, client_conf=None, base_url=None):
        '''初始化'''
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode="rb"):
        """打开文件时使用"""
        pass

    def _save(self, name, content):
        """name 要保存的文件名
           content 包含上传文件内容的一个file的对象
        """
        # 创建一个fdfs_client对象 配置文件的位置是基于dailyfresh的
        client = Fdfs_client(self.client_conf)

        # 使用client上传文件内容到fdfs服务器上 返回的结果是一个字典
        res = client.upload_by_buffer(content.read())

        """
        return dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : '',
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        }
        """

        if res.get("Status") != 'Upload successed.':
            raise Exception("上传文件到fdfs失败")
        else:
            filename = res.get("Remote file_id")
            return filename

    def exists(self, name):
        """django判断文件名是否可用
            如果已存在返回True
        """
        return False  # 自定义为文件名永远可用

    def url(self, name):
        """url函数返回保存了的文件的文件名"""
        return self.base_url+name

