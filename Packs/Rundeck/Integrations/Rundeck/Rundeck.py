import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

import json
import urllib3
import dateparser
import traceback
from typing import Any, Dict, Tuple, List, Optional, Union, cast
import ntpath

# Disable insecure warnings
urllib3.disable_warnings()

''' CONSTANTS '''

VERSION = 24

''' CLIENT CLASS '''


class Client(BaseClient):
    """Client class to interact with the service API

    This Client implements API calls, and does not contain any Demisto logic.
    Should only do requests and return data.
    It inherits from BaseClient defined in CommonServer Python.
    Most calls use _http_request() that handles proxy, SSL verification, etc.
    For this HelloWorld implementation, no special attributes defined
    """

    def __init__(self, base_url, project_name, params, verify=True, proxy=False, ok_codes=tuple(), headers=None,
                 auth=None):
        self.project_name = project_name
        self.params = params
        super().__init__(base_url, verify, proxy, ok_codes, headers, auth)

    def get_project_list(self):
        return self._http_request(
            method='GET',
            url_suffix=f'/projects',
            params=self.params
        )

    def get_webhooks_list(self, project_name):
        if project_name:
            project_name_to_pass = project_name
        else:
            project_name_to_pass = self.project_name
        return self._http_request(
            method='GET',
            url_suffix=f'/project/{self.project_name_to_pass}/webhooks',
            params=self.params
        )

    def get_jobs_list(self, id_list: list, group_path: str, job_filter: str, job_exec_filter: str,
                      group_path_exact: str,
                      scheduled_filter: str, server_node_uuid_filter: str):
        """
        This function returns a list of all existing projects.
        :param id_list: list of Job IDs to include
        :param group_path: include all jobs within that group path. if not specified, default is: "*".
        :param job_filter: specify a filter for a job Name, apply to any job name that contains this value
        :param job_exec_filter: specify an exact job name to match
        :param group_path_exact: specify an exact group path to match. if not specified, default is: "*".
        :param scheduled_filter: return only scheduled or only not scheduled jobs. can either be "true" or "false
        :param server_node_uuid_filter: return all jobs related to a selected server UUID".
        :return: api response.
        """
        request_params: Dict[str, Any] = {}

        if id_list:
            request_params['idlist'] = ','.join(id_list)
        if group_path:
            request_params['groupPath'] = group_path
        if job_filter:
            request_params['jobFilter'] = job_filter
        if job_exec_filter:
            request_params['jobExactFilter'] = job_exec_filter
        if group_path_exact:
            request_params['groupPathExact'] = group_path_exact
        if scheduled_filter:
            request_params['scheduledFilter'] = scheduled_filter
        if server_node_uuid_filter:
            request_params['serverNodeUUIDFilter'] = server_node_uuid_filter

        request_params.update(self.params)

        return self._http_request(
            method='GET',
            url_suffix=f'/project/{self.project_name}/jobs',
            params=request_params
        )

    def execute_job(self, job_id: str, arg_string: str, log_level: str, as_user: str, node_filter: str, run_at_time: str, options: dict):
        """
        This function runs an existing job
        :param arg_string: execution arguments for the selected job: -opt1 value1 -opt2 value2
        :param job_id: id of the job you want to execute
        :param log_level: specifying the loglevel to use: 'DEBUG','VERBOSE','INFO','WARN','ERROR'
        :param as_user: identifying the user who ran the job
        :param node_filter: can be a node filter string
        :param run_at_time:  select a time to run the job
        :param options: add options for running a job
        :return: api response
        """
        request_body: Dict[str, Any] = {}

        if arg_string:
            request_body["argString"] = arg_string
        if log_level:
            request_body["loglevel"] = log_level
        if as_user:
            request_body["asUser"] = as_user
        if node_filter:
            request_body["filter"] = node_filter
        if run_at_time:
            request_body["runAtTime"] = run_at_time
        if options:
            request_body["options"] = options

        return self._http_request(
            method='POST',
            url_suffix=f'/job/{job_id}/executions',
            params=self.params,
            data=str(request_body)
        )

    def retry_job(self, job_id: str, arg_string: str, log_level: str, as_user: str, failed_nodes: str, execution_id: str,
                  options: dict):
        """
        This function retry running a failed execution.
        :param arg_string: execution arguments for the selected job: -opt1 value1 -opt2 value2
        :param job_id: id of the job you want to execute
        :param log_level: specifying the log level to use: 'DEBUG','VERBOSE','INFO','WARN','ERROR'
        :param as_user: identifying the user who ran the job
        :param failed_nodes: can either ben true or false. true for run all nodes and false for running only failed nodes
        :param execution_id: for specified what execution to rerun
        :param options: add options for running a job
        :return: api response
        """
        request_body: Dict[str, Any] = {}

        if arg_string:
            request_body["argString"] = arg_string
        if log_level:
            request_body["loglevel"] = log_level
        if as_user:
            request_body["asUser"] = as_user
        if failed_nodes:
            request_body["failedNodes"] = failed_nodes
        if options:
            request_body["options"] = options

        return self._http_request(
            method='POST',
            url_suffix=f'/job/{job_id}/retry/{execution_id}',
            params=self.params,
            data=str(request_body)
        )

    def job_execution_query(self, status_filter: str, aborted_by_filter: str, user_filter: str, recent_filter: str,
                            older_filter: str, begin: str, end: str, adhoc: str, job_id_list_filter: list,
                            exclude_job_id_list_filter: list, job_list_filter: list, exclude_job_list_filter: list,
                            group_path: str, group_path_exact: str, exclude_group_path: str,
                            exclude_group_path_exact: str, job_filter: str, exclude_job_filter: str,
                            job_exact_filter: str, exclude_job_exact_filter: str, execution_type_filter: str,
                            max_paging: Optional[int], offset: Optional[int], project_name: str):
        """
        This function returns previous and active executions
        :param status_filter: execution status, can be either: "running", succeeded", "failed" or "aborted"
        :param aborted_by_filter: Username who aborted an execution
        :param user_filter: Username who started the execution
        :param recent_filter: for specify when the execution has occur. the format is 'XY' when 'X' is a number and 'Y'
        can be: h - hour, d - day, w - week, m - month, y - year
        :param older_filter: return executions that completed before the specified relative period of time. works with
        the same format as 'recent_filter'
        :param begin: Specify exact date for earliest execution completion time
        :param end: Specify exact date for latest execution completion time
        :param adhoc: can be true or false. true for include Adhoc executions
        :param job_id_list_filter: specify a Job IDs to filter by
        :param exclude_job_id_list_filter: specify a Job IDs to exclude
        :param job_list_filter: specify a full job group/name to include.
        :param exclude_job_list_filter: specify a full Job group/name to exclude
        :param group_path: specify a group or partial group to include all jobs within that group path.
        :param group_path_exact: like 'group_path' but you need to specify an exact group path to match
        :param exclude_group_path specify a group or partial group path to exclude all jobs within that group path
        :param exclude_group_path_exact: specify a group or partial group path to exclude jobs within that group path
        :param job_filter: provide here a job name to query
        :param exclude_job_filter: provide here a job name to exclude
        :param job_exact_filter: provide here an exact job name to match
        :param exclude_job_exact_filter: specify an exact job name to exclude
        :param execution_type_filter: specify the execution type, can be: 'scheduled', 'user' or 'user-scheduled'
        :param max_paging: maximum number of results to get from the api
        :param offset: offset for first result to include
        :param project_name: the project name that you want to get its execution
        :return: api response
        """

        request_params: Dict[str, Any] = {}

        if status_filter:
            request_params['statusFilter'] = status_filter
        if aborted_by_filter:
            request_params['abortedbyFilter'] = aborted_by_filter
        if user_filter:
            request_params['userFilter'] = user_filter
        if recent_filter:
            request_params['recentFilter'] = recent_filter
        if older_filter:
            request_params['olderFilter'] = older_filter
        if begin:
            request_params['begin'] = begin
        if end:
            request_params['end'] = end
        if adhoc:
            request_params['adhoc'] = adhoc
        if job_id_list_filter:
            request_params['jobIdListFilter'] = job_id_list_filter
        if exclude_job_id_list_filter:
            request_params['excludeJobIdListFilter'] = exclude_job_id_list_filter
        if job_list_filter:
            request_params['jobListFilter'] = job_list_filter
        if exclude_job_list_filter:
            request_params['excludeJobListFilter'] = exclude_job_list_filter
        if group_path:
            request_params['groupPath'] = group_path
        if group_path_exact:
            request_params['groupPathExact'] = group_path_exact
        if exclude_group_path:
            request_params['excludeGroupPath'] = exclude_group_path
        if exclude_group_path_exact:
            request_params['excludeGroupPathExact'] = exclude_group_path_exact
        if job_filter:
            request_params['jobFilter'] = job_filter
        if exclude_job_filter:
            request_params['excludeJobFilter'] = exclude_job_filter
        if job_exact_filter:
            request_params['jobExactFilter'] = job_exact_filter
        if exclude_job_exact_filter:
            request_params['excludeJobExactFilter'] = exclude_job_exact_filter
        if execution_type_filter:
            request_params['executionTypeFilter'] = execution_type_filter
        if max_paging:
            request_params['max'] = max_paging
        if offset:
            request_params['offset'] = offset
        if project_name:
            project_name_to_pass = project_name
        else:
            project_name_to_pass = self.project_name

        request_params.update(self.params)

        return self._http_request(
            method='POST',
            url_suffix=f'/project/{project_name_to_pass}/executions',
            params=request_params,
        )

    def job_execution_output(self, execution_id):
        """
        This function gets metadata regarding workflow state
        :param execution_id: id to execute.
        :return: api response
        """
        return self._http_request(
            method='GET',
            url_suffix=f'/execution/{execution_id}/output/state',
            params=self.params,
        )

    def job_execution_abort(self, execution_id):
        """
        This function aborts live executions
        :param execution_id: id to abort execution
        :return: api response
        """
        return self._http_request(
            method='GET',
            url_suffix=f'/execution/{execution_id}/abort',
            params=self.params,
        )

    def adhoc_run(self, project_name: str, exec_command: str, node_thread_count: str, node_keepgoing: str, as_user: str,
                  node_filter: str):
        """
        This function executes shell commands in nodes.
        :param project_name: project to run the command on
        :param exec_command: the shell command that you want to run
        :param node_thread_count: threadcount to use
        :param node_keepgoing: 'true' for continue executing on other nodes after a failure. 'false' otherwise
        :param as_user: specifies a username identifying the user who ran the command
        :param node_filter: node filter to add
        :return: api response
        """
        request_params: Dict[str, Any] = {}

        if exec_command:
            request_params['exec'] = exec_command
        if node_thread_count:
            request_params['nodeThreadcount'] = node_thread_count
        if node_keepgoing:
            request_params['nodeKeepgoing'] = node_keepgoing
        if as_user:
            request_params['asUser'] = as_user
        if node_filter:
            request_params['filter'] = node_filter
        if project_name:
            project_name_to_pass = project_name
        else:
            project_name_to_pass = self.project_name

        request_params.update(self.params)

        return self._http_request(
            method='GET',
            url_suffix=f'/project/{project_name_to_pass}/run/command',
            params=request_params,
        )

    def adhoc_script_run_from_url(self, project_name: str, script_url: str, node_thread_count: str, node_keepgoing: str,
                                  as_user: str, node_filter: str, script_interpreter: str, interpreter_args_quoted: str,
                                  file_extension: str, arg_string: str):
        """
        This function runs a script downloaded from a URL
        :param project_name: project to run the command on
        :param script_url: a URL pointing to a script file
        :param node_thread_count: threadcount to use
        :param node_keepgoing: 'true' for continue executing on other nodes after a failure. false otherwise
        :param as_user: specifies a username identifying the user who ran the command
        :param node_filter: node filter string
        :param script_interpreter: a command to use to run the script
        :param interpreter_args_quoted: if true, the script file and arguments will be quoted as the last argument to
        the script_interpreter. false otherwise.
        :param file_extension: extension of the script file
        :param arg_string: arguments to pass to the script when executed.
        :return: api response
        """
        request_params: Dict[str, Any] = {}

        if node_thread_count:
            request_params['nodeThreadcount'] = node_thread_count
        if node_keepgoing:
            request_params['nodeKeepgoing'] = node_keepgoing
        if as_user:
            request_params['asUser'] = as_user
        if node_filter:
            request_params['filter'] = node_filter
        if script_interpreter:
            request_params['scriptInterpreter'] = script_interpreter
        if interpreter_args_quoted:
            request_params['interpreterArgsQuoted'] = interpreter_args_quoted
        if file_extension:
            request_params['fileExtension'] = file_extension
        if arg_string:
            request_params['argString'] = arg_string
        if project_name:
            project_name_to_pass = project_name
        else:
            project_name_to_pass = self.project_name

        request_params.update(self.params)
        self._headers['Content-Type'] = 'application/x-www-form-urlencoded'

        return self._http_request(
            method='POST',
            data={'scriptURL': script_url},
            url_suffix=f'/project/{project_name_to_pass}/run/url',
            params=request_params,
        )

    def webhook_event_send(self, auth_token: str):
        """
        This function posts data to the webhook endpoint
        :param auth_token: data that you want to post
        :return: api response
        """
        return self._http_request(
            method='POST',
            url_suffix=f'/webhook/{auth_token}',
            params=self.params,
        )

    def adhoc_script_run(self, project_name: str, arg_string: str, node_thread_count: str, node_keepgoing: str, as_user: str, node_filter: str
                                     ,script_interpreter: str, interpreter_args_quoted: str, file_extension: str, entry_id: str):
        """
        This function runs a script from file
        :param project_name: project to run the script file
        :param arg_string: arguments for the script when executed
        :param node_thread_count: threadcount to use
        :param node_keepgoing: 'true' for continue executing on other nodes after a failure. false otherwise
        :param as_user: identifying the user who ran the job
        :param node_filter:
        :param script_interpreter: a command to use to run the script
        :param interpreter_args_quoted: if true, the script file and arguments will be quoted as the last argument to
        :param file_extension: extension of of the script file
        :param entry_id: Demisto id for the uploaded script file you want to run
        :return: api response
        """

        request_params: Dict[str, any] = {}
        if arg_string:
            request_params['argString'] = arg_string
        if node_thread_count:
            request_params['nodeThreadcount'] = node_thread_count
        if node_keepgoing:
            request_params['nodeKeepgoing'] = node_keepgoing
        if as_user:
            request_params['asUser'] = as_user
        if script_interpreter:
            request_params['scriptInterpreter'] = script_interpreter
        if interpreter_args_quoted:
            request_params['interpreterArgsQuoted'] = interpreter_args_quoted
        if file_extension:
            request_params['fileExtension'] = file_extension
        if node_filter:
            request_params['filter'] = node_filter
        if project_name:
            project_name_to_pass = project_name
        else:
            project_name_to_pass = self.project_name

        file_path = demisto.getFilePath(entry_id).get("path", None)
        if not file_path:
            raise DemistoException(
                f"Could not find file path to the next entry id: {entry_id}. \n"
                f"Please provide another one."
            )
        else:
            file_name = ntpath.basename(file_path)

        request_params.update(self.params)
        del self._headers['Content-Type']
        with open(file_path, "rb") as file:
            self._headers.update({'Content-Disposition': f'form-data; name="file"; filename="{file_name}"'})
            return self._http_request(
                method="POST",
                files={'scriptFile': file},
                url_suffix=f'/project/{project_name_to_pass}/run/script',
                params=request_params
            )


''' HELPER FUNCTIONS '''


def filter_results(results: Union[list, dict], fields_to_remove: list, remove_signs) -> Union[list, dict]:
    new_results = []
    if isinstance(results, dict):
        new_record = {}
        for key, value in results.items():
            if key not in fields_to_remove:
                if isinstance(value, dict):
                    value = filter_results(value, fields_to_remove, remove_signs)
                for sign in remove_signs:
                    if sign in key:
                        new_record[key.replace(sign, '')] = value
                    else:
                        new_record[key] = value
        return new_record
    else:
        for record in results:
            new_record = {}
            for key, value in record.items():
                if key not in fields_to_remove:
                    if isinstance(value, dict):
                        value = filter_results(value, fields_to_remove, remove_signs)
                    for sign in remove_signs:
                        if sign in key:
                            new_record[key.replace(sign, '')] = value
                        else:
                            new_record[key] = value
            new_results.append(new_record)
    return new_results


def attribute_pairs_to_dict(attrs_str: Optional[str], delim_char: str = ","):
    """
    Transforms a string of multiple inputs to a dictionary list

    :param attrs_str: attributes separated by key=val pairs sepearated by ','
    :param delim_char: delimiter character between atrribute pairs
    :return:
    """
    if not attrs_str:
        return attrs_str
    attrs = {}
    regex = re.compile(r"(.*)=(.*)")
    for f in attrs_str.split(delim_char):
        match = regex.match(f)
        if match is None:
            raise ValueError(f"Could not parse field: {f}")

        attrs.update({match.group(1): match.group(2)})

    return attrs


def convert_str_to_int(val_to_convert: Optional[str], param_name: str) -> Optional[int]:
    if val_to_convert:
        try:
            return int(val_to_convert)
        except ValueError:
            raise DemistoException(f'\'{param_name}\' most be a number.')


''' COMMAND FUNCTIONS '''


def job_retry_command(client: Client, args: dict):
    arg_string: str = args.get('arg_string', '')
    log_level: str = args.get('log_level', '')  # TODO: add list options 'DEBUG','VERBOSE','INFO','WARN','ERROR'
    as_user: str = args.get('as_user', '')
    failed_nodes: str = args.get('failed_nodes', '')  # TODO: add list options 'true' or 'false'
    job_id: str = args.get('job_id')
    execution_id: str = args.get('execution_id')
    options: str = args.get('options')

    converted_options: dict = attribute_pairs_to_dict(options)
    result = client.retry_job(job_id, arg_string, log_level, as_user, failed_nodes, execution_id, converted_options)
    if not isinstance(result, dict):
        raise DemistoException(f"Got unexpected output from api: {result}")

    query_entries: list = createContext(
        result, keyTransform=string_to_context_key
    )
    headers = [key.replace("-", " ") for key in [*result.keys()]]

    readable_output = tableToMarkdown('Execute Job:', result, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.ExecutedJobs',
        outputs=query_entries,
        outputs_key_field='id'
    )


def execute_job_command(client: Client, args: dict):
    arg_string: str = args.get('arg_string', '')
    log_level: str = args.get('log_level', '')  # TODO: add list options 'DEBUG','VERBOSE','INFO','WARN','ERROR'
    as_user: str = args.get('as_user', '')
    node_filter: str = args.get('filter', '')
    run_at_time: str = args.get('run_at_time', '')
    options: str = args.get('options')
    job_id: str = args.get('job_id')

    converted_options: dict = attribute_pairs_to_dict(options)
    result = client.execute_job(job_id, arg_string, log_level, as_user, node_filter, run_at_time, converted_options)
    if not isinstance(result, dict):
        raise DemistoException(f"Got unexpected output from api: {result}")

    filtered_results = filter_results(result, ['href', 'permalink'], ['-'])

    headers = [key.replace("-", " ") for key in [*filtered_results.keys()]]

    readable_output = tableToMarkdown('Execute Job:', filtered_results, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.ExecutedJobs',
        outputs=filtered_results,
        outputs_key_field='id'
    )


def project_list_command(client: Client):
    """
    This function returns a list of all existing projects.
    :param client: Demisto client
    :return: CommandResults object
    """
    result: list = client.get_project_list()
    if not isinstance(result, list):
        raise DemistoException(f"Got unexpected output from api: {result}")

    filtered_results = filter_results(result, ['url'], ['-'])

    headers = [key.replace("_", " ") for key in [*filtered_results[0].keys()]]

    readable_output = tableToMarkdown('Projects List:', filtered_results, headers=headers,
                                      headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.Projects',
        outputs=filtered_results,
        outputs_key_field='name'
    )


def jobs_list_command(client: Client, args: dict):
    """
    This function returns a list of all existing jobs.
    :param client: Demisto client
    :param args: command's arguments
    :return: CommandResults object
    """
    id_list: list = argToList(args.get('id_list', []))
    group_path: str = args.get('group_path', '')
    job_filter: str = args.get('job_filter', '')
    job_exec_filter: str = args.get('job_exec_filter', '')
    group_path_exact: str = args.get('group_path_exact', '')
    scheduled_filter: str = args.get('scheduled_filter', '')  # ￿￿￿￿￿ TODO: set it as list option 'true' or 'false'
    server_node_uuid_filter: str = args.get('server_node_uuid_filter', '')

    result = client.get_jobs_list(id_list, group_path, job_filter, job_exec_filter, group_path_exact, scheduled_filter,
                                  server_node_uuid_filter)
    if not isinstance(result, list):
        raise DemistoException(f"Got unexpected output from api: {result}")

    filtered_results = filter_results(result, ['href', 'permalink'], ['-'])

    headers = [key.replace("_", " ") for key in [*filtered_results[0].keys()]]

    readable_output = tableToMarkdown('Jobs List:', filtered_results, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.Jobs',
        outputs=filtered_results,
        outputs_key_field='Id'
    )


def webhooks_list_command(client: Client, args: dict):
    """
    This function returns a list of all existing webhooks.
    :param client: Demisto client
    :return: CommandResults object
    """
    project_name: str = args.get('project_name', '')
    result = client.get_webhooks_list(project_name)

    if not isinstance(result, list):
        raise DemistoException(f"Got unexpected output from api: {result}")

    headers = [key.replace("_", " ") for key in [*result[0].keys()]]

    readable_output = tableToMarkdown('Webhooks List:', result, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.Webhooks',
        outputs=result,
        outputs_key_field='id'
    )


def job_execution_query_command(client: Client, args: dict):
    """
    This function returns a list of all existing executions.
    :param client: Demisto client
    :param args: command's arguments
    :return: CommandResults object
    """
    status_filter: str = args.get('status_filter', '')  # TODO: add a list options: "running", succeeded", "failed" or "aborted"
    aborted_by_filter: str = args.get('aborted_by_filter', '')
    user_filter: str = args.get('user_filter', '')
    recent_filter: str = args.get('recent_filter', '')
    older_filter: str = args.get('older_filter', '')
    begin: str = args.get('begin', '')
    end: str = args.get('end', '')
    adhoc: str = args.get('adhoc', '')  # TODO: add list options: true or false
    job_id_list_filter: list = argToList(args.get('job_id_list_filter', []))
    exclude_job_id_list_filter: list = argToList(args.get('exclude_job_id_list_filter', []))
    job_list_filter: list = argToList(args.get('job_list_filter', []))
    exclude_job_list_filter: list = argToList(args.get('exclude_job_list_filter', []))
    group_path: str = args.get('group_path', '')
    group_path_exact: str = args.get('group_path_exact', '')
    exclude_group_path_exact: str = args.get('exclude_group_path_exact', '')
    job_filter: str = args.get('job_filter', '')
    exclude_job_filter: str = args.get('exclude_job_filter', '')
    job_exact_filter: str = args.get('job_exact_filter', '')
    exclude_job_exact_filter: str = args.get('exclude_job_exact_filter', '')
    execution_type_filter: str = args.get('execution_type_filter', '')  #￿￿￿ TODO: add list options: scheduled, user, user-scheduled
    max_paging: Optional[int] = convert_str_to_int(args.get('max_paging'), 'max')
    offset: Optional[int] = convert_str_to_int(args.get('offset'), 'offset')
    project_name: str = args.get('project_name', '')
    exclude_group_path: str = args.get('exclude_group_path', '')

    result = client.job_execution_query(status_filter, aborted_by_filter, user_filter, recent_filter, older_filter,
                                        begin, end, adhoc, job_id_list_filter, exclude_job_id_list_filter,
                                        job_list_filter, exclude_job_list_filter,
                                        group_path, group_path_exact, exclude_group_path,
                                        exclude_group_path_exact, job_filter, exclude_job_filter,
                                        job_exact_filter, exclude_job_exact_filter, execution_type_filter,
                                        max_paging, offset, project_name)

    if isinstance(result, dict):
        result = result.get('executions')
        if not result:
            return "No results were found"

    filtered_results = filter_results(result, ['href', 'permalink'], ['-'])
    if isinstance(result, list):
        headers = [key.replace("_", " ") for key in [*filtered_results[0].keys()]]
    elif isinstance(result, dict):
        headers = [key.replace("_", " ") for key in [*filtered_results.keys()]]
    else:
        raise DemistoException(f'Got unexpected results from the api: {result}')

    readable_output = tableToMarkdown('Job Execution Query:', filtered_results, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.Query',
        outputs=filtered_results,
        outputs_key_field='id'
    )


def job_execution_output_command(client: Client, args: dict):
    """
    This function gets metadata regarding workflow state
    :param client: demisto client object
    :param args: command's arguments
    :return: CommandRusult object
    """
    execution_id: Optional[int] = convert_str_to_int(args.get('execution_id'), 'execution_id')
    result = client.job_execution_output(execution_id)

    if isinstance(result, dict):
        headers = [key.replace("_", " ") for key in [*result.keys()]]
    elif isinstance(result, list):
        headers = [key.replace("_", " ") for key in [*result[0].keys()]]

    readable_output = tableToMarkdown('Job Execution Output:', result, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.ExecutionsOutput',
        outputs=result,
        outputs_key_field='id'
    )


def job_execution_abort_command(client: Client, args: dict):
    """
    This function abort an active execution
    :param client: demisto client object
    :param args: command's arguments
    :return: CommandRusult object
    """
    execution_id: Optional[int] = convert_str_to_int(args.get('execution_id'), 'execution_id')
    result = client.job_execution_abort(execution_id)
    if not isinstance(result, dict):
        raise DemistoException(f'Got unexpected response: {result}')

    filtered_results = filter_results(result, ['href', 'permalink'], ['-'])
    headers = [key.replace("_", " ") for key in [*filtered_results.keys()]]
    readable_output = tableToMarkdown('Job Execution Abort:', filtered_results, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.Aborted',
        outputs=filtered_results,
        outputs_key_field='id'
    )


def adhoc_run_command(client: Client, args: dict):
    project_name: str = args.get('project_name', '')
    exec_command: str = args.get('exec', '')
    node_thread_count: str = args.get('node_thread_count', '')
    node_keepgoing: str = args.get('node_keepgoing', '')  # TODO: add list option true\false
    as_user: str = args.get('as_user')
    node_filter: str = args.get('node_filter', '')

    result = client.adhoc_run(project_name, exec_command, node_thread_count, node_keepgoing, as_user, node_filter)
    # if not isinstance(result, dict):
        # raise DemistoException(f'Got unexpected response: {result}')

    filtered_results = filter_results(result, ['href', 'permalink'], ['-'])
    headers = [key.replace("_", " ") for key in [*filtered_results.keys()]]
    readable_output = tableToMarkdown('Adhoc Run:', filtered_results, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.ExecuteCommand',
        outputs=filtered_results,
        outputs_key_field='id'
    )


def adhoc_script_run_command(client: Client, args: dict):
    project_name: str = args.get('project_name', '')
    arg_string: str = args.get('arg_string', '')
    node_thread_count: str = args.get('node_thread_count', '')
    node_keepgoing: str = args.get('node_keepgoing', '')  # TODO: add list option true\false
    as_user: str = args.get('as_user')
    script_interpreter: str = args.get('script_interpreter', '')
    interpreter_args_quoted: str = args.get('interpreter_args_quoted', '')  # TODO: add list option true\false
    file_extension: str = args.get('file_extension', '')
    node_filter: str = args.get('node_filter', '')
    entry_id: str = args.get('entry_id', '')

    result = client.adhoc_script_run(project_name, arg_string, node_thread_count, node_keepgoing, as_user, node_filter
                                     , script_interpreter, interpreter_args_quoted, file_extension, entry_id)
    # if not isinstance(result, dict):
    # raise DemistoException(f'Got unexpected response: {result}')

    filtered_results = filter_results(result, ['href', 'permalink'], ['-'])
    headers = [key.replace("_", " ") for key in [*filtered_results.keys()]]
    readable_output = tableToMarkdown('Adhoc Run Script:', filtered_results, headers=headers,
                                      headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.ExecuteScriptFile',
        outputs=filtered_results,
        outputs_key_field='id'
    )


def adhoc_script_run_from_url_command(client: Client, args: dict):
    project_name: str = args.get('project_name', '')
    script_url: str = args.get('script_url', '')
    node_thread_count: str = args.get('node_thread_count', '')
    node_keepgoing: str = args.get('node_keepgoing', '')  # TODO: add list option true\false
    as_user: str = args.get('as_user')
    script_interpreter: str = args.get('script_interpreter', '')
    interpreter_args_quoted: str = args.get('interpreter_args_quoted', '')  # TODO: add list option true\false
    file_extension: str = args.get('file_extension', '')
    node_filter: str = args.get('node_filter', '')
    arg_string: str = args.get('arg_string', '')

    result = client.adhoc_script_run_from_url(project_name, script_url, node_thread_count, node_keepgoing, as_user,
                                              node_filter, script_interpreter, interpreter_args_quoted, file_extension,
                                              arg_string)
    # if not isinstance(result, dict):
    # raise DemistoException(f'Got unexpected response: {result}')

    headers = [key.replace("_", " ") for key in [*result.keys()]]
    readable_output = tableToMarkdown('Adhoc Run Script From Url:', result, headers=headers, headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.ScriptExecutionFromUrl',
        outputs=result,
        outputs_key_field='id'
    )


def webhook_event_send_command(client: Client, args: dict):
    auth_token = args.get('auth_token', '')

    result = client.webhook_event_send(auth_token)

    headers = [key.replace("_", " ") for key in [*result.keys()]]
    readable_output = tableToMarkdown('Adhoc Run Script From Url:', result, headers=headers,
                                      headerTransform=pascalToSpace)
    return CommandResults(
        readable_output=readable_output,
        outputs_prefix='Rundeck.WebhookEvent',
        outputs=result,
        outputs_key_field='id'
    )


def test_module(client: Client) -> str:
    try:
        client.get_project_list()
    except DemistoException as e:
        if 'unauthorized' in str(e):
            return 'Authorization Error: make sure your token is correctly set'
        else:
            raise e
    else:
        return 'ok'


''' MAIN FUNCTION '''


def main() -> None:
    """main function, parses params and runs command functions

    :return:
    :rtype:
    """
    params: dict = demisto.params()
    token: str = params.get('token')
    project_name: str = params.get('project_name')

    # get the service API url
    base_url: str = urljoin(demisto.params()['url'], f'/api/{VERSION}')

    # if your Client class inherits from BaseClient, SSL verification is
    # handled out of the box by it, just pass ``verify_certificate`` to
    # the Client constructor
    verify_certificate = not demisto.params().get('insecure', False)

    # out of the box by it, just pass ``proxy`` to the Client constructor
    proxy = demisto.params().get('proxy', False)

    # INTEGRATION DEVELOPER TIP
    # You can use functions such as ``demisto.debug()``, ``demisto.info()``,
    # etc. to print information in the XSOAR server log. You can set the log
    # level on the server configuration
    # See: https://xsoar.pan.dev/docs/integrations/code-conventions#logging

    args: Dict = demisto.args()
    demisto.debug(f'Command being called is {demisto.command()}')
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        client = Client(
            base_url=base_url,
            verify=verify_certificate,
            headers=headers,
            proxy=proxy,
            params={'authtoken': f'{token}'},
            project_name=project_name)

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client)
            return_results(result)
        elif demisto.command() == 'rundeck-projects-list':
            result = project_list_command(client)
            return_results(result)
        elif demisto.command() == 'rundeck-jobs-list':
            result = jobs_list_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-webhooks-list':
            result = webhooks_list_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-job-execute':
            result = execute_job_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-job-retry':
            result = job_retry_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-job-executions-query':
            result = job_execution_query_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-job-execution-output':
            result = job_execution_output_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-job-execution-abort':
            result = job_execution_abort_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-adhoc-command-run':
            result = adhoc_run_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-adhoc-script-run':
            result = adhoc_script_run_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-adhoc-script-run-from-url':
            result = adhoc_script_run_from_url_command(client, args)
            return_results(result)
        elif demisto.command() == 'rundeck-webhook-event-send':
            result = webhook_event_send_command(client, args)
            return_results(result)

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()