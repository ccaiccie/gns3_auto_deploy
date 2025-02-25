
import requests
import json
import telnetlib
import time
import datetime
import urllib3
import ipaddress
import os
import logging.handlers
import sqlite3


from modules.gns3_variables import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# region Functions: Utilities
def make_request(method, url, data=None):
    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)  # Add json=data here
    elif method == "PUT":
        response = requests.put(url, json=data)
    elif method == "DELETE":
        response = requests.delete(url)
    else:
        raise ValueError("Invalid method")
    response.raise_for_status()
    if response.content:
        return response.json()
    else:
        return {}


def log_and_update_db(server_name, project_name, deployment_type, deployment_status, deployment_step, log_message):
    # Log the message using logging.info
    logging.info(log_message)

    # Insert a new record into the deployments table
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    insert_query = '''
        INSERT INTO deployments (server_name, project_name, deployment_type, deployment_status, deployment_step, log_message)
        VALUES (?, ?, ?, ?, ?, ?);
    '''

    c.execute(insert_query, (server_name, project_name, deployment_type, deployment_status, deployment_step, log_message))
    conn.commit()
    conn.close()

def util_extract_csr(response):
    json_data = response.json()
    if 'data' in json_data:
        return json_data['data']
    else:
        raise Exception(f"Failed to extract CSR. Response: {json_data}")


def util_print_response(response_data):
    if response_data.content:
        json_data = response_data.json()
        logging.info(json.dumps(json_data, indent=4))
    else:
        logging.info("Response content is empty.")


def util_get_file_size(file_path):
    size = os.path.getsize(file_path)
    size_name = ["B", "KB", "MB", "GB"]
    i = 0
    while size > 1024:
        size = size / 1024
        i += 1
    return f"{size:.2f} {size_name[i]}"


def util_resume_time(delay_time):
    resume_time = (datetime.datetime.now() + datetime.timedelta(minutes=delay_time)).strftime("%H:%M:%S")
    return resume_time


def util_current_time():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return current_time


# endregion

# region Functions: GNS3 API Functions
def gns3_create_project(gns3_server_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {"name": project_name}
        node_url = f"http://{server_ip}:{server_port}/v2/projects"
        node_response = make_request("POST", node_url, data=template_data)
        project_id = node_response["project_id"]
        return project_id

def gns3_create_project_static(server_ip, server_port, project_name):
    template_data = {"name": project_name}
    node_url = f"http://{server_ip}:{server_port}/v2/projects"
    node_response = make_request("POST", node_url, data=template_data)
    project_id = node_response["project_id"]
    return project_id

def gns3_create_project_test():
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {"name": project_name}
        node_url = f"http://{server_ip}:{server_port}/v2/projects"
        node_response = make_request("POST", node_url, data=template_data)
        project_id = node_response["project_id"]
        return project_id

def gns3_create_drawing(gns3_server_data, project_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
        node_response = make_request("POST", node_url, data=node_data)


def gns3_create_node(gns3_server_data, project_id, template_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        logging.info(f"Deploy - Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id


def gns3_create_node_multi_return(gns3_server_data, project_id, template_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/templates/{template_id}"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        logging.info(f"Deploy - Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id, node_name


def gns3_create_cloud_node(gns3_server_data, project_id, node_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
        node_response = make_request("POST", node_url, data=node_data)
        node_name = node_response["name"]
        logging.info(f"Deploy - Created Node {node_name}")
        node_id = node_response["node_id"]
        return node_id


def gns3_create_template(gns3_server_data, template_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/templates"
        node_response = make_request("POST", node_url, data=template_data)
        template_id = node_response["template_id"]
        template_name = node_response["name"]
        logging.info(f"Deploy - Created template {template_name}")
        return template_id


def gns3_connect_nodes(gns3_server_data, project_id, node_a, adapter_a, port_a, node_b, adapter_b, port_b):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/links"
        node_data = {"nodes": [{"adapter_number": adapter_a, "node_id": node_a, "port_number": port_a},
                               {"adapter_number": adapter_b, "node_id": node_b, "port_number": port_b}]}
        node_a_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_a)
        node_b_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_b)
        logging.info(f"Deploy - Connected (adapter/port) {adapter_a}/{port_a} of {node_a_name[0]} to (adapter/port) {adapter_b}/{port_b} of {node_b_name[0]}")
        node_response = make_request("POST", node_url, data=node_data)
        return node_response["link_id"]


def gns3_delete_nodes(gns3_server_data, project_id, delete_node_name):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        matching_nodes = gns3_find_nodes_by_name(gns3_server_data, delete_node_name)
        if matching_nodes:
            for node_id, console_port, aux in matching_nodes:
                delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
                response = make_request("DELETE", delete_url)
                node_name = response["name"]
                logging.info(f"Deleted node {node_name} on GNS3 Server {server_ip}")
        else:
            logging.info(f"Deploy - No nodes with '{delete_node_name}' in their name were found in project {project_name} on GNS3 Server {server_ip}")


def gns3_delete_all_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        nodes = gns3_get_nodes(gns3_server_data, project_id)
        for node in nodes:
            node_id = node['node_id']
            delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
            response = make_request("DELETE", delete_url)
            node_name = node["name"]
            logging.info(f"Deploy - Deleted node {node_name} on GNS3 Server {server_ip}")


def gns3_delete_all_drawings(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        drawings = gns3_get_drawings(gns3_server_data, project_id)
        for drawing in drawings:
            drawing_id = drawing['drawing_id']
            delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings/{drawing_id}"
            response = make_request("DELETE", delete_url)
            logging.info(f"Deploy - Deleted drawing {drawing_id} on GNS3 Server {server_ip}")


def gns3_delete_template(gns3_server_data, template_name):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_id = gns3_get_template_id(gns3_server_data, template_name)
        if template_id:
            delete_url = f"http://{server_ip}:{server_port}/v2/templates/{template_id}"
            make_request("DELETE", delete_url)
            logging.info(f"Deploy - Deleted template ID {template_name} on GNS3 Server {server_ip}")
        else:
            logging.info(f"No templates with '{template_name}' in their name were found on GNS3 Server {server_ip}")


def gns3_delete_project(gns3_server_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        project_id = gns3_get_project_id(gns3_server_data)
        if project_id:
            delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
            make_request("DELETE", delete_url)
            logging.info(f"Deploy - Deleted project ID {project_name} on GNS3 Server {server_ip}")
        else:
            logging.info(f"No projects with '{project_name}' in their name were found on GNS3 Server {server_ip}")

def gns3_delete_project_static(server_ip, server_port, project_name, project_id):
    if project_id:
        delete_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
        make_request("DELETE", delete_url)
        logging.info(f"Deploy - Deleted project ID {project_name} on GNS3 Server {server_ip}")
    else:
        logging.info(f"No projects with '{project_name}' in their name were found on GNS3 Server {server_ip}")


def gns3_find_nodes_by_name(gns3_server_data, project_id, search_string=None):
    node_data = gns3_get_nodes(gns3_server_data, project_id)
    if search_string:
        matching_nodes = [node for node in node_data if search_string in node['name']]
        if not matching_nodes:
            return []
        else:
            return [(node['node_id'], node['console'], node['properties'].get('aux')) for node in matching_nodes]
    else:
        return []


def gns3_get_location_data(gns3_server_data, project_id, item_type):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/{item_type}"
        response = requests.get(url)
        data = json.loads(response.text)
        nodes = []
        if item_type == 'nodes':
            for node in data:
                name = node['name']
                x = node['x']
                y = node['y']
                z = node['z']
                nodes.append({'name': name, 'x': x, 'y': y, 'z': z})
        elif item_type == 'drawings':
            for node in data:
                svg = node['svg']
                x = node['x']
                y = node['y']
                z = node['z']
                nodes.append({'svg': svg, 'x': x, 'y': y, 'z': z})
        location_data = nodes
        drawing_data = {}
        for i, item_data in enumerate(location_data):
            drawing_key = f"drawing_{i + 1:02}"
            drawing_data[drawing_key] = item_data

        logging.info("\n".join([f'"{k}": {json.dumps(v, separators=(",", ":"))},' for k, v in drawing_data.items()]))
        return nodes


def gns3_find_nodes_by_field(gns3_server_data, project_id, search_field, return_field, search_string):
    nodes = gns3_get_nodes(gns3_server_data, project_id)
    if search_string:
        matching_nodes = [node for node in nodes if search_string in node[search_field]]
        if not matching_nodes:
            return []
        else:
            return [(node[return_field]) for node in matching_nodes]
    else:
        return []


def gns3_get_project_id(gns3_server_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects"
        response = requests.get(url)
        projects = json.loads(response.text)
        for project in projects:
            if project['name'] == project_name:
                return project['project_id']
        return None


def gns3_get_template_id(gns3_server_data, template_name):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/templates"
        response = requests.get(url)
        templates = json.loads(response.text)
        for template in templates:
            if template['name'] == template_name:
                return template['template_id']
        return None


def gns3_get_drawings(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/drawings"
        response = requests.get(url)
        if not response.ok:
            logging.info(f"Error retrieving links: {response.status_code}")
            exit()
        try:
            nodes = response.json()
        except ValueError as e:
            logging.info(f"Error parsing JSON: {e}")
            logging.info(f"Response content: {response.content}")
            exit()
        return nodes


def gns3_get_image(gns3_server_data, image_type, filename):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}"
        response = requests.get(url)

        return response.status_code


def gns3_get_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes"
        response = requests.get(url)
        if not response.ok:
            logging.info(f"Error retrieving links: {response.status_code}")
            exit()
        try:
            nodes = response.json()
        except ValueError as e:
            logging.info(f"Error parsing JSON: {e}")
            logging.info(f"Response content: {response.content}")
            exit()
        return nodes


def gns3_get_node_files(gns3_server_data, project_id, node_id, file_path):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/files/{file_path}"
        response = requests.get(url)
        if not response.ok:
            logging.info(f"Error retrieving links: {response.status_code}")
            exit()
        try:
            nodes = response.json()
        except ValueError as e:
            logging.info(f"Error parsing JSON: {e}")
            logging.info(f"Response content: {response.content}")
            exit()
        return nodes


def gns3_reload_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/reload"
        response = make_request("POST", node_url, data={})
        logging.info(f"Reloaded node {node_id}")


def gns3_upload_symbol(gns3_server_data, symbol_file, symbol_name):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f'http://{server_ip}:{server_port}/v2/symbols/{symbol_name}/raw'
        headers = {"accept": "*/*"}
        response = requests.post(url, headers=headers, data=symbol_file)
        if response.status_code == 204:
            logging.info(f'Deploy - Uploaded symbol {symbol_name}')
            return
        else:
            logging.info(f'Deploy - Failed to upload {symbol_name}. Status code: {response.status_code}')


def gns3_upload_file_to_node(gns3_server_data, project_id, node_id, file_path_var, filename_temp):
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), 'configs/')
    file_path = os.path.join(configs_path, filename_temp)
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        # Set the file path and name to be written to the node
        node_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_id)

        # Set the API endpoint URL for the node file write
        url = f'http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/files/{file_path_var}'

        # Open the local file and read its content
        with open(file_path, 'r') as f:
            file_content = f.read()

        # Set the API request headers and payload
        headers = {"accept": "application/json"}
        request_data = file_content.encode('utf-8')

        # Send the API request to write the file to the node
        response = requests.post(url, headers=headers, data=request_data)

        # Check if the API request was successful
        if response.status_code == 201:
            logging.info(f'Deploy - File - {filename_temp} successfully written to the node {node_name[0]}')
            return
        else:
            logging.info(f'Deploy - Failed to write file to the node {node_name[0]}. Status code: {response.status_code}')


def gns3_upload_image(gns3_server_data, image_type, filename):
    image_file_path = f'images/{image_type}'
    abs_path = os.path.abspath(__file__)
    configs_path = os.path.join(os.path.dirname(abs_path), image_file_path)
    file_path = os.path.join(configs_path, filename)
    file_size = util_get_file_size(file_path)
    logging.info(f"File Size: {file_size}")
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        url = f'http://{server_ip}:{server_port}/v2/compute/{image_type}/images/{filename}'
        response = gns3_get_image(gns3_server_data, image_type, filename)
        if response != 200:
            headers = {"accept": "*/*"}
            logging.info(f'Deploy - Image - {filename} being uploaded to server. Please wait..')
            response = requests.post(url, headers=headers, data=open(file_path, "rb"))
            if response.status_code == 204:
                logging.info(f'Deploy - Image - {filename} successfully written to server')
                return
            else:
                logging.info(f'Deploy - Failed to write file to the server. Status code: {response.status_code}')


def gns3_update_nodes(gns3_server_data, project_id, node_id, request_data):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        request_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}"
        node_name = gns3_find_nodes_by_field(gns3_server_data, project_id, 'node_id', 'name', node_id)
        request_response = make_request("PUT", request_url, data=request_data)
        logging.info(f"Deploy - Updated deploy data for node {node_name[0]}")


def gns3_start_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/start"
        node_response = make_request("POST", node_url, data=template_data)


def gns3_stop_node(gns3_server_data, project_id, node_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/{node_id}/stop"
        node_response = make_request("POST", node_url, data=template_data)


def gns3_start_all_nodes(gns3_server_data, project_id):
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP']
        template_data = {}
        logging.info(f"Deploy - Starting all nodes in project {project_name}")
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}/nodes/start"
        node_response = make_request("POST", node_url, data=template_data)
        logging.info(f"Deploy - Started all nodes in project {project_name}")


def gns3_set_project(gns3_server_data, project_id):
    logging.info(gns3_server_data)
    for server_record in gns3_server_data:
        server_ip, server_port, project_name, vmanage_api_ip, vedge_count = server_record['GNS3 Server'], server_record[
            'Server Port'], server_record['Project Name'], server_record['vManage API IP'], server_record['Site Count']
        if vedge_count is None:
            project_zoom = 80
            project_scene_height = 1000
            project_scene_width = 2000
        elif vedge_count <= 30:
            project_zoom = 57
            project_scene_height = 1000
            project_scene_width = 2000
        else:
            project_zoom = 30
            project_scene_height = 1500
            project_scene_width = 4200
        template_data = {"auto_close": False, "scene_height": project_scene_height,
                         "scene_width": project_scene_width,
                         "zoom": project_zoom}
        node_url = f"http://{server_ip}:{server_port}/v2/projects/{project_id}"
        node_response = make_request("PUT", node_url, data=template_data)
        project_id = node_response["project_id"]
        logging.info(f"Deploy - Update project settings for {project_name}")
        return project_id


def gns3_actions_upload_images(gns3_server_data):
    for root, dirs, files in os.walk("images/"):
        for file_name in files:
            image_type = os.path.basename(root)
            logging.info(f"image_type:{image_type}, filename: {file_name}")
            gns3_upload_image(gns3_server_data, image_type, file_name)


def gns3_actions_remove_templates(gns3_server_data):
    gns3_delete_template(gns3_server_data, vmanage_template_name)
    gns3_delete_template(gns3_server_data, vbond_template_name)
    gns3_delete_template(gns3_server_data, vsmart_template_name)
    gns3_delete_template(gns3_server_data, vedge_template_name)
    gns3_delete_template(gns3_server_data, cisco_l3_router_template_name)
    gns3_delete_template(gns3_server_data, network_test_tool_template_name)
    gns3_delete_template(gns3_server_data, open_vswitch_cloud_template_name)
    gns3_delete_template(gns3_server_data, mgmt_hub_template_name)
    gns3_delete_template(gns3_server_data, mgmt_main_hub_template_name)
    gns3_delete_template(gns3_server_data, arista_ceos_template_name)
    delete_more_than_1_var = 0
    if delete_more_than_1_var == 1:
        while True:
            template_id = gns3_get_template_id(gns3_server_data, arista_ceos_template_name)
            if not template_id:
                break
            gns3_delete_template(gns3_server_data, arista_ceos_template_name)


# endregion

# region Generate Dynamic Data for Deployment

# endregion