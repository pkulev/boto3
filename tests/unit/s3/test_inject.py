# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License'). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the 'license' file accompanying this file. This file is
# distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from tests import unittest
import mock

from botocore.exceptions import ClientError

from boto3.s3 import inject


class TestInjectTransferMethods(unittest.TestCase):
    def test_inject_upload_download_file_to_client(self):
        class_attributes = {}
        inject.inject_s3_transfer_methods(class_attributes=class_attributes)
        self.assertIn('upload_file', class_attributes)
        self.assertIn('download_file', class_attributes)

    def test_upload_file_proxies_to_transfer_object(self):
        with mock.patch('boto3.s3.inject.S3Transfer') as transfer:
            inject.upload_file(mock.sentinel.CLIENT,
                               Filename='filename',
                               Bucket='bucket', Key='key')
            transfer.return_value.upload_file.assert_called_with(
                filename='filename', bucket='bucket', key='key',
                extra_args=None, callback=None)

    def test_download_file_proxies_to_transfer_object(self):
        with mock.patch('boto3.s3.inject.S3Transfer') as transfer:
            inject.download_file(
                mock.sentinel.CLIENT,
                Bucket='bucket', Key='key',
                Filename='filename')
            transfer.return_value.download_file.assert_called_with(
                bucket='bucket', key='key', filename='filename',
                extra_args=None, callback=None)


class TestBucketLoad(unittest.TestCase):
    def setUp(self):
        self.client = mock.Mock()
        self.resource = mock.Mock()
        self.resource.meta.client = self.client

    def test_bucket_load_finds_bucket(self):
        self.resource.name = 'MyBucket'
        self.client.list_buckets.return_value = {
            'Buckets': [
                {'Name': 'NotMyBucket', 'CreationDate': 1},
                {'Name': self.resource.name, 'CreationDate': 2},
            ],
        }

        inject.bucket_load(self.resource)
        self.assertEqual(
            self.resource.meta.data,
            {'Name': self.resource.name, 'CreationDate': 2})

    def test_bucket_load_raise_error(self):
        self.resource.name = 'MyBucket'
        self.client.list_buckets.return_value = {
            'Buckets': [
                {'Name': 'NotMyBucket', 'CreationDate': 1},
                {'Name': 'NotMine2', 'CreationDate': 2},
            ],
        }
        with self.assertRaises(ClientError):
            inject.bucket_load(self.resource)
