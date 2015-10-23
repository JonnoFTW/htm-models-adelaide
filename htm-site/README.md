HTM Adelaide Webapp 
===================

Installation
------------
1. Make sure you're a VM (preferably the one you set up for the engine component)
2. Run `python setup.py develop`
3. Run the server with `pserve development.ini`
4. Access the site on http://127.0.0.1:8070

Optional nginx setup
--------------------
Based on the instructions here: http://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/deployment/nginx.html
1. Make sure you've got nginx installed and running
2. Your config in `/etc/nginx/conf.d/htmsite.conf` should look like:

```
upstream htm-site {
    server 127.0.0.1:8070
}
server {

    listen 8080;

    access_log  /home/example/env/access.log;

    location / {
        proxy_set_header        Host $http_host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;

        client_max_body_size    10m;
        client_body_buffer_size 128k;
        proxy_connect_timeout   60s;
        proxy_send_timeout      90s;
        proxy_read_timeout      90s;
        proxy_buffering         off;
        proxy_temp_file_write_size 64k;
        proxy_pass http://htm-site;
        proxy_redirect          off;
    }
    location /static {
        root                    /home/example/htm-models-adelaide/htmsite/assets;
        expires                 30d;
        add_header              Cache-Control public;
        access_log              off;
    }
}
```
3. Restart nginx using `service nginx restart`