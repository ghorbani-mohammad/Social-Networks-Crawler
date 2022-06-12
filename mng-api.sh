#!/bin/bash

PROJECT_NAME='social'
SERVER_NAME='VPS74001'
PROJECT_PATH='/root/army/social/'

API_CONTAINER_NAME=${PROJECT_NAME}'_api'
DB_CONTAINER_NAME=${PROJECT_NAME}'_db'
CELERY_CONTAINER_NAME=${PROJECT_NAME}'_celery'
CELERY_BEAT_CONTAINER_NAME=${PROJECT_NAME}'_beat'
REDIS_CONTAINER_NAME=${PROJECT_NAME}'_redis'

COMPOSE_FILE='docker-compose.yml'
NGINX_FILE='social_api_nginx.conf'


function log() {
    docker-compose -f ${COMPOSE_FILE} logs -f
}

function make_migrations() {
    docker exec -it ${API_CONTAINER_NAME} ./${PROJECT_NAME}/manage.py makemigrations
}

function showmigrations() {
    echo -e "\n ... showmigrations ... \n"
    docker exec -it ${API_CONTAINER_NAME} ./${PROJECT_NAME}/manage.py showmigrations $1
}

function migrate() {
    echo -e "\n ... migrate db ... \n"
    docker exec -t $1 ./${PROJECT_NAME}/manage.py migrate $2 $3
}

function bash() {
    docker exec -it -w /app/${PROJECT_NAME} ${API_CONTAINER_NAME} bash
}

function shell() {
    docker exec -it ${API_CONTAINER_NAME} ./${PROJECT_NAME}/manage.py shell
}

function drop_db() {
    docker exec -it ${DB_CONTAINER_NAME} psql -U postgres -c "drop schema public cascade;"
    docker exec -it ${DB_CONTAINER_NAME} psql -U postgres -c "create schema public;"
}

function populate_db() {
    cat $1 | docker exec -i ${DB_CONTAINER_NAME} psql -U postgres
}

function collectstatic() {
    echo -e "\n ... collect static files ... \n"
    docker exec -i $1 ./${PROJECT_NAME}/manage.py collectstatic --noinput
}

function create_admin_user() {
    docker exec -it ${API_CONTAINER_NAME} ./${PROJECT_NAME}/manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('${1:-admin}', '', '${2:-test1234}')"
}

function issue_https_certificate() {
    sudo certbot --nginx certonly -d social.rasad-project.ir
    sudo ln -s ${PROJECT_PATH}${NGINX_FILE} /etc/nginx/sites-enabled/${NGINX_FILE}
    sudo service nginx restart
}

function dump_db() {
    echo -e "\n ... dump db ... \n"
    mkdir -p db_backup
    docker exec -t ${DB_CONTAINER_NAME} pg_dumpall -c -U postgres | gzip > ./db_backup/${PROJECT_NAME}_db_`date +\%d-\%m-\%Y"_"\%H_\%M_\%S`.sql.gz
}

function pull() {
    echo -e "\n ... pull images ... \n"
    docker-compose -f ${COMPOSE_FILE} pull ${API_CONTAINER_NAME} ${CELERY_CONTAINER_NAME} ${CELERY_BEAT_CONTAINER_NAME}
}

function up() {
    echo -e "\n ... up containers ... \n"
    docker-compose -f ${COMPOSE_FILE} up -d
}

function remove_unused_image() {
    echo -e "\n ... remove unused images ... \n"
    docker image prune -af
}

function scp_conf() {
    echo -e "\n ... copy conf files to server ... \n"
    scp ${COMPOSE_FILE} ${NGINX_FILE} mng-api.sh doc.json .docpasswd ${SERVER_NAME}:${PROJECT_PATH}
}

case $1 in
scp_conf)
    scp_conf
;;
up_remote)
    ssh -t ${SERVER_NAME} "cd ${PROJECT_PATH}; ./mng-api.sh up"
;;
up)
    pull
    dump_db
    up
    migrate ${API_CONTAINER_NAME}
    collectstatic ${API_CONTAINER_NAME}
    remove_unused_image
;;
log)
    log
;;
makemigrations)
    make_migrations
;;
showmigrations)
    showmigrations $2
;;
migrate)
    migrate ${API_CONTAINER_NAME} $2 $3
;;
bash)
    bash
;;
shell)
    shell
;;
drop_db)
    drop_db
;;
populate_db)
    populate_db $2
;;
admin_user)
    create_admin_user $2 $3
;;
https)
    issue_https_certificate
;;
dump_db)
    dump_db
;;
down)
    docker container rm -f ${API_CONTAINER_NAME} ${REDIS_CONTAINER_NAME} ${CELERY_CONTAINER_NAME} ${CELERY_BEAT_CONTAINER_NAME}; docker container stop ${DB_CONTAINER_NAME}
;;
*)
    echo "don't know what to do"
;;
esac
