import os
import json
import configparser
from looker_sdk import client, models


### ---- Enter the IDs of Looks in the look_ids array --------------
looks_ids = [1830, 1831]



###-----------Do not change the code down here :-) -----------------
def get_access_token():
    
    client_id = config['Looker']['client_id']
    client_secret = config['Looker']['client_secret']
    base_url = config['Looker']['base_url']
    
    # Get access token
    token = os.popen(f'curl -X POST "{base_url}/login?client_id={client_id}&client_secret={client_secret}"')
    token = token.readlines()
    token = token[0].split(':')
    token = token[1].split(',')
    token = token[0].replace('"', '')
    
    return token

def get_viz_config(look_id):
    
    token = get_access_token()
    base_url = config['Looker']['base_url']
    
    look = os.popen(f'curl -i -H "Authorization: token {token}" {base_url}/api/3.1/looks/{look_id}')
    look = look.readlines()
    
    look_data = json.loads(look[13])
    
    viz_config = look_data.get('query')
    viz_config = viz_config.get('vis_config')
    
    return viz_config


def main(sdk_old_instance, sdk_new_instance, look_id):
    
    old_instance_viz = get_viz_config(look_id=look_id)
    
    # Get the Look from DCL instance
    old_look = sdk_old_instance.look(look_id=look_id)
    old_query = old_look.query
    
    # Get the user who created the ID
    old_user_id = old_look.user
    old_user_info = sdk_old_instance.user(user_id=old_user_id.id)

    ## Find user in Local instance based on email:
    cred = old_user_info.email
    new_user = sdk_new_instance.user_for_credential(credential_type='email', credential_id=cred)

    # User's info in New instance
    user_id = new_user.id
    folder_id = new_user.personal_space_id

    # Create Folder in new instance
    to_new_folder = 'Looks moved with API'
    try:
        folder = models.WriteFolder(name=to_new_folder, parent_id=folder_id)
        _ = sdk_new_instance.create_folder(body=folder)
    except:
        pass

    # Find the ID of the created folder
    new_folder = sdk_new_instance.search_folders(name=to_new_folder)
    new_folder_id = new_folder[0].id

    # Build Query's body
    create_query = models.WriteQuery(model= old_query.model, view = old_query.view, fields = old_query.fields, pivots= old_query.pivots, fill_fields= old_query.fill_fields, filters = old_query.filters, filter_expression = old_query.filter_expression, sorts = old_query.sorts, limit = old_query.limit, column_limit = old_query.column_limit, total = old_query.total, row_total= old_query.row_total, subtotals = old_query.subtotals, vis_config = old_instance_viz, filter_config = old_query.filter_config, visible_ui_sections = old_query.visible_ui_sections, dynamic_fields = old_query.dynamic_fields)

    # Get new query's info
    new_query = sdk_new_instance.create_query(body=create_query)

    # Build Look's body
    look_body = models.WriteLookWithQuery(title=old_look.title, is_run_on_load=True, query_id=new_query.id, space_id=new_folder_id, user_id=user_id, query=create_query)

    # Create Look
    _ = sdk_new_instance.create_look(body=look_body)

    print(f"Congratulation for moving Look: {look_id} to the new instance")
    

# Configure SDK Client for the old_instance
sdk_old_instance = client.setup("dcl.ini")

# Configure SDK Client for the new_instance
sdk_new_instance = client.setup("local.ini")

config = configparser.ConfigParser()
config.read('dcl.ini')

for look in look_ids:
    main(sdk_old_instance=sdk_old_instance, sdk_new_instance=sdk_new_instance, look_id=look)