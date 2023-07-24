
import json
import os

import requests
import streamlit as st
from shared.constants import SERVER, InternalFileType, InternalResponse, ServerType

from utils.constants import AUTH_TOKEN, AUTH_TOKEN, LOGGED_USER
from utils.local_storage.url_storage import delete_url_param, get_url_param


class APIRepo:
    def __init__(self):
        import dotenv
        dotenv.load_dotenv()

        SERVER_URL = os.getenv('SERVER_URL', '')
        self.base_url = SERVER_URL

        self._setup_urls()

    def _setup_urls(self):
        # user
        self.USER_OP_URL = '/v1/user/op'
        self.USER_LIST_URL = '/v1/user/list'

        # payment
        self.ORDER_OP_URL = '/v1/payment/order'
        self.ORDER_LIST_URL = '/v1/payment/order/list'
        
        # auth
        self.AUTH_OP_URL = '/v1/authentication/op'
        self.AUTH_REFRESH_URL = '/v1/authentication/refresh'
        self.GOOGLE_LOGIN_URL = '/v1/authentication/google'

        # timing
        self.TIMING_URL = '/v1/data/timing'
        self.PROJECT_TIMING_URL = '/v1/data/timing/project'
        self.TIMING_NUMBER_URL = '/v1/data/timing/number'
        self.SHIFT_TIMING_URL = '/v1/data/timing/shift'
        self.TIMING_LIST_URL = '/v1/data/timing/list'

        # project
        self.PROJECT_URL = '/v1/data/project'
        self.PROJECT_LIST_URL = '/v1/data/project/list'
        
        # project setting
        self.PROJECT_SETTING_URL = '/v1/data/project-setting'
        
        # inference log
        self.LOG_URL = '/v1/data/log'
        self.LOG_LIST_URL = '/v1/data/log/list'
        
        # file
        self.FILE_URL = '/v1/data/file'
        self.FILE_LIST_URL = '/v1/data/file/list'
        self.FILE_UUID_LIST_URL = '/v1/data/file/uuid-list'
        self.FILE_UPLOAD_URL = 'v1/data/file/upload'
        
        # app setting
        self.APP_SETTING_URL = '/v1/data/app-setting'
        self.APP_SECRET_URL = '/v1/data/app-secret'
        
        # ai model
        self.MODEL_URL = '/v1/data/model'
        self.MODEL_LIST_URL = '/v1/data/model/list'

    def logout(self):
        delete_url_param(AUTH_TOKEN)
        st.experimental_rerun()

    ################### base http methods
    def _get_headers(self, content_type="application/json"):
        auth_token = get_url_param(AUTH_TOKEN)
        if not auth_token and SERVER != ServerType.DEVELOPMENT.value:
            self.logout()

        headers = {}
        headers["Authorization"] = f"Bearer {auth_token}"
        if content_type:
            headers["Content-Type"] = content_type

        return headers

    def http_get(self, url, params = None):
        res = requests.get(self.base_url + url, params = params, headers=self._get_headers())
        return res.json()

    def http_post(self, url, data = {}, file_content = None):
        if file_content:
            files = {file_content}
            res = requests.post(self.base_url + url, json=data, files=files, headers=self._get_headers(None))
        else:
            res = requests.post(self.base_url + url, json=data, headers=self._get_headers())

        return res.json()
    
    def http_put(self, url, data = None):
        res = requests.put(self.base_url + url, json=data, headers=self._get_headers())
        return res.json()
    
    def http_delete(self, url, params=None):
        res = requests.delete(self.base_url + url, params=params, headers=self._get_headers())
        return res.json()

    #########################################
    def google_user_login(self, **kwargs):
        headers = {}
        headers["Content-Type"] = "application/json"
        res = requests.post(self.base_url + self.GOOGLE_LOGIN_URL, json=kwargs, headers=headers)
        payload = { 'data': None }
        res_json = json.loads(res._content)
        if res.status_code == 200 and res_json['status']:
            payload = { 'data': res_json['payload']}
        return InternalResponse(payload, 'user login successfully', res_json['status'])

    def create_user(self, **kwargs):
        res = self.http_post(url=self.USER_OP_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    # making it fetch the current logged in user
    def get_first_active_user(self):
        res = self.http_get(self.USER_OP_URL)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_user_by_email(self, email):
        res = self.http_get(self.USER_OP_URL, params={'email': email})
        return InternalResponse(res['payload'], 'user fetched successfully', True)
    
    def get_total_user_count(self):
        res = self.http_get(self.USER_LIST_URL)
        payload = res['payload']['count'] if 'count' in res['payload'] else 0
        return InternalResponse(payload, 'user count fetched successfully', True)
    
    def get_all_user_list(self):
        res = self.http_get(self.USER_LIST_URL)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    # TODO: remove this method from everywhere
    def delete_user_by_email(self, email):
        res = self.db_repo.delete_user_by_email(email)
        return InternalResponse(res['payload'], 'success', res['status']).status

    # internal file object
    # TODO: remove this method from everywhere
    def get_file_from_name(self, name):
        pass

    def get_file_from_uuid(self, uuid):
        res = self.http_get(self.FILE_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_all_file_list(self, type: InternalFileType, tag = None, project_id = None):
        filter_data = {"type": type}
        if tag:
            filter_data['tag'] = tag
        if project_id:
            filter_data['project_id'] = project_id

        res = self.http_get(self.FILE_LIST_URL, params=filter_data)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def create_or_update_file(self, uuid, type=InternalFileType.IMAGE.value, **kwargs):
        update_data = kwargs
        update_data['uuid'] = uuid
        update_data['type'] = type
        res = self.http_put(url=self.FILE_URL, data=update_data)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def upload_file(self, file_content):
        res = self.http_post(url=self.FILE_UPLOAD_URL, data={}, file_content=file_content)
        return InternalResponse(res['payload'], 'success', res['status'])
        
    def create_file(self, **kwargs):
        res = self.http_post(url=self.FILE_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def delete_file_from_uuid(self, uuid):
        res = self.db_repo.delete_file_from_uuid(uuid)
        return InternalResponse(res['payload'], 'success', res['status']).status
    
    # TODO: remove file_type from this method
    def get_image_list_from_uuid_list(self, image_uuid_list, file_type=InternalFileType.IMAGE.value):
        res = self.http_get(self.FILE_UUID_LIST_URL, params={'uuid_list': image_uuid_list, 'type': file_type})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def update_file(self, **kwargs):
        res = self.http_put(url=self.FILE_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    # project
    def get_project_from_uuid(self, uuid):
        res = self.http_get(self.PROJECT_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_all_project_list(self, user_id):
        res = self.http_get(self.PROJECT_LIST_URL, params={'user_id': user_id})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def create_project(self, **kwargs):
        res = self.http_post(url=self.PROJECT_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def delete_project_from_uuid(self, uuid):
        res = self.http_delete(self.PROJECT_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    # ai model (custom ai model)
    def get_ai_model_from_uuid(self, uuid):
        res = self.http_get(self.MODEL_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    # TODO: remove this method from everywhere
    def get_ai_model_from_name(self, name):
        res = self.http_get(self.MODEL_URL, params={'name': name})
        return InternalResponse(res['payload'], 'success', res['status'])

    
    def get_all_ai_model_list(self, model_type=None, user_id=None):
        res = self.http_get(self.MODEL_LIST_URL, params={'user_id': user_id})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def create_ai_model(self, **kwargs):
        res = self.http_post(url=self.MODEL_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def update_ai_model(self, **kwargs):
        res = self.http_put(url=self.MODEL_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def delete_ai_model_from_uuid(self, uuid):
        res = self.http_delete(self.MODEL_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status']).status

    # inference log
    def get_inference_log_from_uuid(self, uuid):
        res = self.http_get(self.LOG_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_all_inference_log_list(self, project_id=None, model_id=None):
        res = self.http_get(self.LOG_LIST_URL, params={'project_id': project_id, 'model_id': model_id})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def create_inference_log(self, **kwargs):
        res = self.http_post(url=self.LOG_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def delete_inference_log_from_uuid(self, uuid):
        res = self.db_repo.delete_inference_log_from_uuid(uuid)
        return InternalResponse(res['payload'], 'success', res['status']).status
    
    # TODO: complete this
    def get_ai_model_param_map_from_uuid(self, uuid):
        pass
    
    def get_all_ai_model_param_map_list(self, model_id=None):
        pass
    
    def create_ai_model_param_map(self, **kwargs):
        pass
    
    def delete_ai_model(self, uuid):
        pass
    

    # timing
    def get_timing_from_uuid(self, uuid):
       res = self.http_get(self.TIMING_URL, params={'uuid': uuid})
       return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_timing_from_frame_number(self, project_uuid, frame_number):
        res = self.http_get(self.PROJECT_TIMING_URL, params={'project_id': project_uuid, 'frame_number': frame_number})
        return InternalResponse(res['payload'], 'success', res['status']) 
    
    # this is based on the aux_frame_index and not the order in the db
    def get_next_timing(self, uuid):
        res = self.http_get(self.TIMING_NUMBER_URL, params={'uuid': uuid, 'distance': 1})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_prev_timing(self, uuid):
        res = self.http_get(self.TIMING_NUMBER_URL, params={'uuid': uuid, 'distance': -1})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_timing_list_from_project(self, project_uuid=None):
        res = self.http_get(self.TIMING_LIST_URL, params={'project_id': project_uuid, 'page': 1})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def create_timing(self, **kwargs):
        res = self.http_post(url=self.TIMING_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def update_specific_timing(self, uuid, **kwargs):
        kwargs['uuid'] = uuid
        res = self.http_put(url=self.TIMING_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])

    def delete_timing_from_uuid(self, uuid):
        res = self.http_delete(self.TIMING_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status']).status
    
    # removes all timing frames from the project
    def remove_existing_timing(self, project_uuid):
        res = self.http_delete(self.PROJECT_TIMING_URL, params={'uuid': project_uuid})
        return InternalResponse(res['payload'], 'success', res['status']).status
    
    def remove_primay_frame(self, timing_uuid):
        update_data = {
            'uuid': timing_uuid,
            'primary_image_id': None
        }
        res = self.http_put(self.TIMING_URL, data=update_data)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def remove_source_image(self, timing_uuid):
        update_data = {
            'uuid': timing_uuid,
            'source_image_id': None
        }
        res = self.http_put(self.TIMING_URL, data=update_data)
        return InternalResponse(res['payload'], 'success', res['status'])

    def move_frame_one_step_forward(self, project_uuid, index_of_frame):
        data = {
            "project_id": project_uuid,
            "index_of_frame": index_of_frame
        }
        
        res = self.http_post(self.SHIFT_TIMING_URL, data=data)
        return InternalResponse(res['payload'], 'success', res['status'])
    

    # app setting
    def get_app_setting_from_uuid(self, uuid=None):
        res = self.http_get(self.APP_SETTING_URL, params={'uuid': uuid})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def get_app_secrets_from_user_uuid(self, uuid=None):
        res = self.http_get(self.APP_SECRET_URL)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    # TODO: complete this code
    def get_all_app_setting_list(self):
        pass
    
    def update_app_setting(self, **kwargs):
        res = self.http_put(url=self.APP_SETTING_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def create_app_setting(self, **kwargs):
        res = self.http_post(url=self.APP_SETTING_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])

    def delete_app_setting(self, user_id):
        res = self.db_repo.delete_app_setting(user_id)
        return InternalResponse(res['payload'], 'success', res['status']).status
    

    # setting
    def get_project_setting(self, project_id):
        res = self.http_get(self.PROJECT_SETTING_URL, params={'uuid': project_id})
        return InternalResponse(res['payload'], 'success', res['status'])
    
    # TODO: add valid model_id check throughout dp_repo
    def create_project_setting(self, **kwargs):
        res = self.http_post(url=self.PROJECT_SETTING_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])
    
    def update_project_setting(self, **kwargs):
        res = self.http_put(url=self.PROJECT_SETTING_URL, data=kwargs)
        return InternalResponse(res['payload'], 'success', res['status'])

    # TODO: update or remove this
    def bulk_update_project_setting(self, **kwargs):
        pass
    

    # backup
    # TODO: complete this
    def get_backup_from_uuid(self, uuid):
        pass
    
    def create_backup(self, project_uuid, version_name):
        # backup = self.db_repo.create_backup(project_uuid, version_name).data['data']
        # return InternalBackupObject(**backup) if backup else None
        return None
    
    def get_backup_list(self, project_id=None):
        # backup_list = self.db_repo.get_backup_list(project_id).data['data']
        # return [InternalBackupObject(**backup) for backup in backup_list] if backup_list else []
        return InternalResponse({'data': []}, 'success', True)
    
    def delete_backup(self, uuid):
        # res = self.db_repo.delete_backup(uuid)
        # return InternalResponse(res['payload'], 'success', res['status']).status
        return True
    
    def restore_backup(self, uuid):
        # res = self.db_repo.restore_backup(uuid)
        # return InternalResponse(res['payload'], 'success', res['status']).status
        return True