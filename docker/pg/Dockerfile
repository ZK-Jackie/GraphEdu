FROM postgres:18.3-trixie

# 安装构建 pgvector 和 Apache AGE 插件所需的依赖，并且替换 apt 镜像源为阿里云以加速下载
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get clean && apt-get update

RUN apt-mark hold locales && \
	apt-get install -y --no-install-recommends bison build-essential flex postgresql-server-dev-18

# 安装 pgvector 插件
ADD https://gh-proxy.org/https://github.com/pgvector/pgvector.git#v0.8.2 /tmp/pgvector

RUN	cd /tmp/pgvector && \
	make clean && \
	make OPTFLAGS="" && \
	make install && \
	mkdir -p /usr/share/doc/pgvector && \
	cp LICENSE README.md /usr/share/doc/pgvector && \
	rm -r /tmp/pgvector

# 安装 Apache AGE 插件
ADD https://gh-proxy.org/https://github.com/apache/age.git#PG18/v1.7.0-rc0 /tmp/age

RUN cd /tmp/age && \
    make clean && \
    make install && \
    mkdir -p /usr/share/doc/age && \
    cp LICENSE README.md /usr/share/doc/age && \
    rm -rf /tmp/age

# 卸载构建插件所需的依赖，并且清理 apt 缓存和不必要的包以减小镜像体积
RUN apt-get remove -y bison build-essential flex postgresql-server-dev-18 && \
    apt-get autoremove -y && \
    apt-mark unhold locales && \
    rm -rf /var/lib/apt/lists/*

# 记得覆盖 CMD 使用配置文件，配置文件中需要启用 `shared_preload_libraries = 'age'` 来加载插件
# 启动后记得在所用的数据库中运行 `CREATE EXTENSION IF NOT EXISTS age;` `CREATE EXTENSION IF NOT EXISTS vector;` 启用插件
