```markdown
# 黔职通自动打卡程序

## 简介
本项目是一个全自动打卡程序，旨在帮助用户自动化完成每日上班和下班的打卡任务。程序具备自动Token续签功能，并通
过PushPlus发送通知，支持多用户同时使用。

## 主要功能
1. **自动打卡**：按照配置的时间自动完成上班和下班的打卡任务。
2. **Token自动续签**：在Token失效或即将过期时，自动获取新的Token并更新配置文件。
3. **PushPlus通知**：通过PushPlus发送打卡成功或失败的通知，确保用户及时了解打卡状态。
4. **多用户支持**：支持多个用户同时配置和使用，每个用户的打卡时间和Token独立管理。

## 使用步骤

### 1. 安装依赖
在使用本项目之前，请确保安装了所需的Python库。您可以通过以下命令安装：
```bash
pip install requests schedule pycryptodome opencv-python-headless
```

### 2. 配置文件
程序启动时会自动生成`config.json`配置文件，用于存储用户的Token、打卡时间和推送通知的相关信息。请根据实际情况修改配置文件中的内容。**注意：生成的默认配置中包含注释，请在填写实际信息前删除这些注释。**

首次运行时，请在配置文件中填写`first_entry_time`、`punch_clock_time`、`phone`、`password`、`pushplus`和`punch_clock_data`等字段，`checkRange`可忽略，例如：
```json
{
    "tokens": [
        {
            "token": "",
            "first_entry_time": "08:31",
            "punch_clock_time": "18:21",
            "messages": [
                {
                    "name": "用户名"
                }
            ],
            "punch_clock_data": {
                "latitude": 32.97672338266904,
                "locationName": "xx公司，建议填写黔职通打卡页面地点名称",
                "longitude": 119.146751801377,
                "checkRange": 99999
            },
            "phone": "10086",
            "password": "123456",
            "last_updated": ""
        }
    ],
    "first_entry_time_data": {},
    "pushplus": {
        "token": "您的PushPlus token",
        "topic": "您的PushPlus topic" 
    }
}
```
请根据实际情况修改配置文件中的相关路径和信息。如果希望配置文件路径为`d:\桌面\config.json`，请在`main.py`的第407行修改如下：
```python
config_path = Path("d:\\桌面\\config.json")  # 配置文件路径
```

### 3. 运行程序
配置完成后，可直接运行`main.py`文件，程序会根据配置文件中的设置自动完成打卡任务。
```bash
python main.py
```

### 4. 更新Token
程序启动时会询问是否需要更新Token，输入`y`将强制更新所有用户的Token。用户也可以根据需要手动更新Token。

## 注意事项
1. 请确保配置文件中的手机号和密码正确无误。
2. 使用PushPlus发送通知时，请确保PushPlus的Token和Topic正确配置。

## 免责声明
本项目仅用于学习和交流目的。使用本项目进行打卡时，请确保您已获得相关系统的授权，并遵守相关法律法规及政策。开发者对于使用本项目产生的任何问题或后果不负责任。
```
