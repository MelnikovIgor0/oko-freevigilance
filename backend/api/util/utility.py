from model.resource import Resource
from config.config import ServerConfig, S3Config
from util.cron import create_cron_job, update_cron_job, kill_cron_job
from model.s3_interactor import get_all_files


def build_query(resource: Resource, server_config: ServerConfig) -> str:
    query = f'python3 {server_config.daemon_path}'
    query += f' -u {resource.url} -r {resource.id}'
    if resource.keywords is not None and len(resource.keywords) > 0:
        query += f' --keywords {",".join(resource.keywords)}'
    if resource.polygon is not None and len(resource.polygon) > 0:
        polygon_str = f'{int(float(resource.polygon[0]["x"]))},{int(float(resource.polygon[0]["y"]))},{int(float(resource.polygon[0]["width"]))},{int(float(resource.polygon[0]["height"]))},{int(float(resource.polygon[0]["sensitivity"]))}'
        query += f' --polygon {polygon_str}'
    return query


def create_daemon_cron_job_for_resource(resource: Resource, server_config: ServerConfig) -> bool:
    query = build_query(resource, server_config)
    print(query, resource.interval, resource.id)
    return create_cron_job(query, resource.interval, resource.id)


def update_daemon_cron_job_for_resource(resource: Resource, server_config: ServerConfig) -> bool:
    if not resource.enabled:
        kill_cron_job(resource.id)
    query = build_query(resource, server_config)
    return update_cron_job(query, resource.interval, resource.id)


def get_last_snapshot_id(cfg: S3Config, resource_id: str) -> int:
    images = get_all_files(cfg, 'images')
    htmls = get_all_files(cfg, 'htmls')
    max_id = 0
    for image in images:
        if image['Key'].startswith(resource_id):
            max_id = max(max_id, int(image['Key'].replace('.', '_').split('_')[1]))
    for html in htmls:
        if html['Key'].startswith(resource_id):
            max_id = max(max_id, int(html['Key'].replace('.', '_').split('_')[1]))
    return max_id
