from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    # 1. 先让 DRF 处理常见异常（校验失败/404/权限），拿到标准响应
    response = exception_handler(exc, context)

    if response is None:
        # 2. DRF 没接住（如数据库异常）→ 兜底 500，避免裸报错/HTML
        response = Response(
            {"code": 500, "message": "服务器内部错误", "data": None},
            status=500,
        )
    else:
        # 3. 提取 DRF 标准错误信息：常见 {"detail":"..."} 或 {"字段":"错误"}
        data = response.data
        message = data.get("detail") or next(iter(data.values()), "请求错误")
        if isinstance(message, (list, tuple)):
            message = message[0]
        # 4. 统一包一层 {code, message, data}
        response.data = {"code": response.status_code, "message": message, "data": data}
    return response