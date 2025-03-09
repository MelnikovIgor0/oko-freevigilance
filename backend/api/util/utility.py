from model.resource import Resource
from config.config import ServerConfig
from util.cron import create_cron_job, update_cron_job


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
    query = build_query(resource, server_config)
    return update_cron_job(query, resource.interval, resource.id)
