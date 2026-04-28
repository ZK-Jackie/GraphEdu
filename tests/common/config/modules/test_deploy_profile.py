"""测试部署配置模块（DeployConfig、DeployImages）。"""

from graphedu.common.config.modules.deploy import DeployConfig, DeployImages


class TestDeployImages:
    """测试 DeployImages 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = DeployImages()

        assert config.postgres == "18.3.0"
        assert config.redis == "8.6.2-alpine"
        assert config.backend == "latest"
        assert config.frontend == "latest"

    def test_custom_versions(self):
        """测试自定义版本。"""
        config = DeployImages(
            postgres="16.1.0",
            redis="7.4.2-alpine",
            backend="1.2.3",
            frontend="1.2.3",
        )

        assert config.postgres == "16.1.0"
        assert config.redis == "7.4.2-alpine"
        assert config.backend == "1.2.3"
        assert config.frontend == "1.2.3"

    def test_partial_override(self):
        """测试部分覆盖。"""
        config = DeployImages(backend="0.5.0")

        assert config.postgres == "18.3.0"
        assert config.backend == "0.5.0"
        assert config.frontend == "latest"

    def test_serialization(self):
        """测试序列化。"""
        config = DeployImages()
        dumped = config.model_dump()

        assert dumped == {
            "postgres": "18.3.0",
            "redis": "8.6.2-alpine",
            "backend": "latest",
            "frontend": "latest",
        }

    def test_json_serialization(self):
        """测试 JSON 序列化。"""
        config = DeployImages(backend="1.0.0")
        json_str = config.model_dump_json()

        assert "1.0.0" in json_str
        assert "18.3.0" in json_str


class TestDeployConfig:
    """测试 DeployConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = DeployConfig()

        assert config.profiles == []
        assert isinstance(config.images, DeployImages)
        assert config.images.postgres == "18.3.0"

    def test_empty_profiles_list(self):
        """测试空的 profiles 列表。"""
        config = DeployConfig(profiles=[])

        assert config.profiles == []

    def test_single_profile(self):
        """测试单个 profile。"""
        config = DeployConfig(profiles=["postgres"])

        assert config.profiles == ["postgres"]

    def test_multiple_profiles(self):
        """测试多个 profiles。"""
        config = DeployConfig(profiles=["postgres", "redis", "neo4j"])

        assert config.profiles == ["postgres", "redis", "neo4j"]

    def test_all_supported_profiles(self):
        """测试所有支持的 profiles。"""
        supported_profiles = ["postgres", "redis", "neo4j", "backend", "frontend"]

        config = DeployConfig(profiles=supported_profiles)

        assert config.profiles == supported_profiles

    def test_profile_postgres(self):
        """测试 PostgreSQL profile。"""
        config = DeployConfig(profiles=["postgres"])

        assert "postgres" in config.profiles

    def test_profile_redis(self):
        """测试 Redis profile。"""
        config = DeployConfig(profiles=["redis"])

        assert "redis" in config.profiles

    def test_profile_neo4j(self):
        """测试 Neo4j profile。"""
        config = DeployConfig(profiles=["neo4j"])

        assert "neo4j" in config.profiles

    def test_profile_backend(self):
        """测试后端 profile。"""
        config = DeployConfig(profiles=["backend"])

        assert "backend" in config.profiles

    def test_profile_frontend(self):
        """测试前端 profile。"""
        config = DeployConfig(profiles=["frontend"])

        assert "frontend" in config.profiles

    def test_custom_profile_string(self):
        """测试自定义 profile（字符串类型允许）。"""
        config = DeployConfig(profiles=["custom-service"])

        assert "custom-service" in config.profiles

    def test_profiles_with_mixed_types(self):
        """测试混合类型的 profiles。"""
        config = DeployConfig(profiles=["postgres", "backend", "monitoring"])

        assert len(config.profiles) == 3
        assert "postgres" in config.profiles
        assert "backend" in config.profiles
        assert "monitoring" in config.profiles

    def test_profiles_duplicates(self):
        """测试重复的 profiles（允许）。"""
        config = DeployConfig(profiles=["postgres", "postgres"])

        assert config.profiles == ["postgres", "postgres"]

    def test_profiles_order(self):
        """测试 profiles 顺序。"""
        config = DeployConfig(profiles=["frontend", "backend", "postgres"])

        assert config.profiles[0] == "frontend"
        assert config.profiles[1] == "backend"
        assert config.profiles[2] == "postgres"

    def test_infrastructure_profiles(self):
        """测试基础设施 profiles。"""
        config = DeployConfig(profiles=["postgres", "redis", "neo4j"])

        assert len(config.profiles) == 3
        assert all(p in config.profiles for p in ["postgres", "redis", "neo4j"])

    def test_application_profiles(self):
        """测试应用 profiles。"""
        config = DeployConfig(profiles=["backend", "frontend"])

        assert len(config.profiles) == 2
        assert "backend" in config.profiles
        assert "frontend" in config.profiles

    def test_full_stack_profiles(self):
        """测试全栈 profiles。"""
        config = DeployConfig(profiles=[
            "postgres",
            "redis",
            "neo4j",
            "backend",
            "frontend",
        ])

        assert len(config.profiles) == 5

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = DeployConfig(profiles=["postgres", "redis"])

        config_dict = config.model_dump()

        assert config_dict["profiles"] == ["postgres", "redis"]
        assert config_dict["images"]["postgres"] == "18.3.0"

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = DeployConfig(profiles=["backend"])

        json_str = config.model_dump_json()

        assert "backend" in json_str

    def test_development_profiles(self):
        """测试开发环境 profiles。"""
        config = DeployConfig(profiles=[
            "postgres",
            "redis",
            "neo4j",
            "backend",
        ])

        # 开发环境通常不包含前端（由开发服务器处理）
        assert "frontend" not in config.profiles

    def test_production_profiles(self):
        """测试生产环境 profiles。"""
        config = DeployConfig(profiles=[
            "postgres",
            "redis",
            "neo4j",
            "backend",
            "frontend",
        ])

        # 生产环境包含所有服务
        assert len(config.profiles) == 5

    def test_minimal_profiles(self):
        """测试最小化 profiles（仅核心服务）。"""
        config = DeployConfig(profiles=["postgres", "backend"])

        assert config.profiles == ["postgres", "backend"]

    def test_profile_case_sensitive(self):
        """测试 profile 大小写敏感。"""
        config1 = DeployConfig(profiles=["Backend"])
        config2 = DeployConfig(profiles=["backend"])

        # Profile 名称是大小写敏感的
        assert config1.profiles == ["Backend"]
        assert config2.profiles == ["backend"]

    def test_profile_with_numbers(self):
        """测试包含数字的 profile。"""
        config = DeployConfig(profiles=["service1", "service2"])

        assert "service1" in config.profiles
        assert "service2" in config.profiles

    def test_profile_with_hyphens(self):
        """测试包含连字符的 profile。"""
        config = DeployConfig(profiles=["custom-service", "micro-service-2"])

        assert "custom-service" in config.profiles
        assert "micro-service-2" in config.profiles

    def test_profile_with_underscores(self):
        """测试包含下划线的 profile。"""
        config = DeployConfig(profiles=["custom_service", "micro_service_2"])

        assert "custom_service" in config.profiles
        assert "micro_service_2" in config.profiles

    def test_profiles_with_images(self):
        """测试 profiles 与 images 共存。"""
        config = DeployConfig(
            profiles=["postgres", "backend"],
            images={"postgres": "16.1.0", "backend": "2.0.0"},
        )

        assert config.profiles == ["postgres", "backend"]
        assert config.images.postgres == "16.1.0"
        assert config.images.backend == "2.0.0"
