FROM postgres:18.3-trixie

ARG APT_MIRROR=mirrors.aliyun.com
ARG GITHUB_PROXY=https://gh-proxy.org

# 替换 APT 镜像源以加速下载（留空使用官方源）
RUN if [ -n "$APT_MIRROR" ]; then \
      sed -i "s/deb.debian.org/$APT_MIRROR/g" /etc/apt/sources.list.d/debian.sources; \
    fi && \
    apt-get clean && apt-get update

RUN apt-mark hold locales && \
	apt-get install -y --no-install-recommends ca-certificates bison build-essential flex git postgresql-server-dev-18 && \
	update-ca-certificates

# 安装 pgvector 插件
RUN BASE="https://github.com/pgvector/pgvector.git"; \
    if [ -n "$GITHUB_PROXY" ]; then BASE="${GITHUB_PROXY}/${BASE}"; fi; \
    git clone "$BASE" --branch v0.8.2 --depth 1 /tmp/pgvector && \
	cd /tmp/pgvector && \
	make clean && \
	make OPTFLAGS="" && \
	make install && \
	mkdir -p /usr/share/doc/pgvector && \
	cp LICENSE README.md /usr/share/doc/pgvector && \
	rm -r /tmp/pgvector

# 安装 Apache AGE 插件
RUN BASE="https://github.com/apache/age.git"; \
    if [ -n "$GITHUB_PROXY" ]; then BASE="${GITHUB_PROXY}/${BASE}"; fi; \
    git clone "$BASE" --branch PG18/v1.7.0-rc0 --depth 1 /tmp/age && \
    cd /tmp/age && \
    make clean && \
    make install && \
    mkdir -p /usr/share/doc/age && \
    cp LICENSE README.md /usr/share/doc/age && \
    rm -rf /tmp/age

# 卸载构建依赖，清理缓存
RUN apt-get remove -y bison build-essential flex git postgresql-server-dev-18 && \
    apt-get autoremove -y && \
    apt-mark unhold locales && \
    rm -rf /var/lib/apt/lists/*
