"""OSS 连接测试工具.

使用说明：
1. 修改下方配置信息
2. 运行脚本: python test_oss_connection.py
"""

# ============= 配置信息 =============
ENDPOINT = "https://8ea8dc52504a6ce4d696aabf96432e1a.r2.cloudflarestorage.com"  # OSS 端点
ACCESS_KEY = "1e1f03dcbaa45a139d06fde6f28ba930"  # 访问密钥 ID
SECRET_KEY = "ab353515a71b85671831c587530ff510fdd318118acdea93ff5c1dc611ed41b4"  # 访问密钥
BUCKET = "difyai"  # 存储桶名称
# =====================================

import boto3
from botocore.exceptions import ClientError

# 创建 S3 客户端
s3 = boto3.client(
    "s3", endpoint_url=ENDPOINT, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name="us-east-1"
)

print("=" * 60)
print("🚀 OSS 连接测试")
print("=" * 60)

# 1. 测试连接
print(f"\n🔍 测试连接: {ENDPOINT}")
try:
    response = s3.list_buckets()
    buckets = [b["Name"] for b in response.get("Buckets", [])]
    print(f"✅ 连接成功！存储桶: {buckets}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
    exit(1)

# 2. 检查存储桶
print(f"\n🔍 检查存储桶: {BUCKET}")
try:
    s3.head_bucket(Bucket=BUCKET)
    print("✅ 存储桶存在")
except ClientError as e:
    if e.response.get("Error", {}).get("Code") == "404":
        print("❌ 存储桶不存在")
    else:
        print(f"❌ 检查失败: {e}")
    exit(1)

# 3. 列出对象
print("\n🔍 列出对象")
try:
    response = s3.list_objects_v2(Bucket=BUCKET)
    objects = response.get("Contents", [])
    print(f"✅ 找到 {len(objects)} 个对象")
    for obj in objects[:5]:
        print(f"   - {obj['Key']} ({obj['Size']} bytes)")
    if len(objects) > 5:
        print(f"   ... 还有 {len(objects) - 5} 个对象")
except Exception as e:
    print(f"❌ 列出失败: {e}")

# 4. 上传测试文件
print("\n🔍 测试上传")
try:
    test_content = b"OSS connection test file"
    s3.put_object(Bucket=BUCKET, Key="test/oss_test.txt", Body=test_content)
    print("✅ 上传成功")
except Exception as e:
    print(f"❌ 上传失败: {e}")
    exit(1)

# 5. 验证上传的文件
print("\n🔍 验证文件")
try:
    obj = s3.head_object(Bucket=BUCKET, Key="test/oss_test.txt")
    print(f"✅ 文件存在，大小: {obj['ContentLength']} bytes")
except Exception as e:
    print(f"❌ 验证失败: {e}")

# 6. 下载文件
print("\n🔍 测试下载")
try:
    response = s3.get_object(Bucket=BUCKET, Key="test/oss_test.txt")
    content = response["Body"].read()
    print(f"✅ 下载成功，内容: {content.decode()}")
except Exception as e:
    print(f"❌ 下载失败: {e}")

# 7. 生成预签名 URL
print("\n🔍 生成预签名 URL")
try:
    url = s3.generate_presigned_url("get_object", Params={"Bucket": BUCKET, "Key": "test/oss_test.txt"}, ExpiresIn=3600)
    print("✅ URL 生成成功:")
    print("   {url[:80]}..." if len(url) > 80 else f"   {url}")
except Exception as e:
    print(f"❌ 生成失败: {e}")

# 8. 删除测试文件
print("\n🔍 删除测试文件")
try:
    s3.delete_object(Bucket=BUCKET, Key="test/oss_test.txt")
    print("✅ 删除成功")
except Exception as e:
    print(f"❌ 删除失败: {e}")

# 9. 测试结果
print("\n" + "=" * 60)
print("📊 测试完成")
print("=" * 60)
print("✅ 所有测试通过！OSS 服务运行正常")
