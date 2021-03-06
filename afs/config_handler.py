import json
from pandas import DataFrame
from afs.flow import flow
import logging

_logger = logging.getLogger(__name__)

class config_handler(object):

    def __init__(self):
        """
Config handler is the class which handle AFS flow framework. User can use function fetch parameters, or send data to next node.
        """
        self.param = []
        self.variable_name = []
        self.column = []
        self.data = DataFrame.empty
        self.type_list = {'string': str, 'integer': int, 'float': float}

    def set_kernel_gateway(self, REQUEST, flow_json_file=None):
        """
For Jupyter kernel gateway API, REQUEST is the request given by kernel gateway. Reference REQUEST: http://jupyter-kernel-gateway.readthedocs.io/en/latest/http-mode.html
        :param REQUEST: JSON type. Jupyter kernel gateway request.
        :param flow_json_file: String of file path. For debug, developer can use file which contains the flow json as the flow json gotten from NodeRed.
        """
        self.flow_obj = flow()

        try:
            headers = json.loads(REQUEST)['headers']
            flow_info = {}
            flow_info['node_id'] = headers['Node_id']
            flow_info['flow_id'] = headers['Flow_id']
            flow_info['host_url'] = headers['Host_url']
            self.flow_obj.set_flow_config(flow_info)
        except Exception as e:
            raise AssertionError('REQUEST must be json format, or headers contains not enough information.')

        if flow_json_file:
            try:
                with open(flow_json_file) as f:
                    flow_json = f.read()
                flow_json = json.loads(flow_json)
                self.flow_obj.get_flow_list_ab(flow_json)
            except Exception as e:
                raise AssertionError('Type error, flow_json must be JSON')
        else:
            try:
                self.flow_obj.get_flow_list()
            except Exception as e:
                raise AssertionError('Request to NodeRed has porblem.')

        self.flow_obj.get_node_item(self.flow_obj.current_node_id)

        try:
            data = json.loads(REQUEST)['body']['data']
            self.data = DataFrame.from_dict(data)
        except Exception as e:
            raise AssertionError('Request contains no key named "data", or cannot transform to dataframe.')

    def get_param(self, key):
        """
Get parameter from the key name, and it should be set from set_param.
        :param key: String type. The parameter key set from method set_param
        :return: Speicfic type depends on set_param. The value of the key name.
        """
        obj_value = self.flow_obj.current_node_obj[key]
        obj_para = [x for x in self.param if x['name'] in key][0]
        try:
            if obj_para['type'] in 'integer':
                obj_value = int(obj_value)
            elif obj_para['type'] in 'string':
                obj_value = str(obj_value)
            elif obj_para['type'] in 'float':
                obj_value = float(obj_value)
            else:
                _logger.warning('Parameter has no specific type.')
                obj_value = str(obj_value)
        except Exception as e:
            raise AssertionError('The value has problem when transfrom type.')

        if obj_value:
            return obj_value
        else:
            return None

    # def get_data(self, request_body):
    #     """
    #
    #     :param request_body:
    #     :return: DataFrame type from REQUEST
    #     """
        # try:
        #     request_body = json.loads(request_body)
        #     if request_body['data']:
        #         self.data = DataFrame.from_dict(request_body['data'])
        #         return self.data
        #     else:
        #         raise AssertionError('Data is not existed in request_body')
        # except Exception as e:
        #     raise AssertionError('Type error, request_body must be JSON')

    def get_data(self):
        """
Transform REQUEST data to DataFrame type.
        :return: DataFrame type. Data from REQUEST and rename column name.
        """
        if self.data is not DataFrame.empty:
            return self.data.rename(columns=self.get_column())
        else:
            return DataFrame.empty

    def get_column(self):
        """
Get the column mapping list.
        :return: Dict type. The value is the column name would use in the AFS API, and the key is the mapping column name.
        """
        return {self.flow_obj.current_node_obj[column_name]: column_name for column_name in self.flow_obj.current_node_obj if column_name in self.column}

    def next_node(self,data, debug=False):
        """
Send data to next node according to flow.
        :param data: DataFrame type.
        :param debug:  bool type. If debug is True, method will return response message from the next node.
        :return: JSON type. Response JSON
        """
        if isinstance(data, DataFrame):
            column_reverse_mapping = {v: k for k, v in self.get_column().items()}
            data = data.rename(columns=column_reverse_mapping)
            data = dict(data=data.to_dict())
            return self.flow_obj.exe_next_node(data, next_list=None, debug=debug)
        else:
            raise AssertionError('Type error, data must be DataFrame type')

    def set_param(self, key, type='string', required=False ,default=None):
        """
Set API parameter will be used in the AFS API.
        :param key: String type. The key name for this parameter
        :param type: String type. The type of the paramter, including integer, string or float.
        :param required: Bool type. The parameter is required or not
        :param default: The parameter is given in default
        """
        if type not in self.type_list:
            raise AssertionError('Type not found.')
        else:
            if not isinstance(default, self.type_list[type]):
                raise AssertionError('Default value is not the specific type.')
        if not isinstance(required, bool):
            raise AssertionError('Required is True/False.')

        # check if the name is the same, raise error
        if key in self.variable_name:
            raise AssertionError('It has already the same name of the parameter.')
        else:
            param = {}
            param['name'] = str(key)
            param['type'] = type
            param['required'] = required
            param['default'] = default
            self.variable_name.append(key)
            self.param.append(param)

    def set_column(self, column_name):
        """
The column name will be used in the AFS API.
        :param column_name: String type. The column name used in the following API
        """
        column_name = str(column_name)
        if column_name in self.variable_name:
            raise AssertionError('It has already the same column name.')
        else:
            self.variable_name.append(column_name)
            self.column.append(column_name)

    def summary(self):
        """
Summary what parameters and column the AFS API need.This method should be called by the last line in the 2nd cell.
        """
        smry = {}
        smry['param'] = self.param
        smry['column'] = self.column
        print(json.dumps(smry))
