```markdown
# 黔职通自动打卡程序

## 简介
本项目是一个全自动打卡程序，旨在帮助用户自动化完成每日的上班和下班打卡任务。系统具备自动Token续签功能，并通过PushPlus
进行通知。支持多用户同时使用。

## 主要功能
1. **全自动打卡**：根据配置的时间自动完成上班和下班的打卡任务。
2. **自动Token续签**：在Token失效或即将过期时，自动获取新的Token并更新配置文件。
3. **PushPlus通知**：通过PushPlus发送打卡成功或失败的通知，确保用户及时了解打卡状况。
4. **多用户支持**：支持多个用户同时配置和使用，每个用户的打卡时间和Token独立管理。

## 使用步骤

### 1. 安装依赖
在使用本项目之前，请确保安装了所需的Python库。您可以通过以下命令安装这些库：
```bash
pip install requests schedule pycryptodome opencv-python-headless
```

### 2. 配置文件
程序启动时会自动生成一个`config.json`配置文件，用于存储用户的Token、打卡时间和推送通知的相关信息。请根据实际情况修改配置文件中的内容，例如：
```json
{
    "tokens": [
        {
            "token": "",
            "first_entry_time": "09:00",
            "punch_clock_time": "18:00",
            "last_updated": null,
            "messages": [
                {
                    "name": "张三",
                    "content": "上班打卡成功",
                    "uid": "张三的uid"
                }
            ],
            "punch_clock_data": {},
            "phone": "13800138000",
            "password": "123456"
        },
        {
            "token": "",
            "first_entry_time": "09:05",
            "punch_clock_time": "18:05",
            "last_updated": null,
            "messages": [
                {
                    "name": "李四",
                    "content": "上班打卡成功",
                    "uid": "李四的uid"
                }
            ],
            "punch_clock_data": {},
            "phone": "13900139000",
            "password": "654321"
        }
    ],
    "pushplus": {
        "token": "您的PushPlus token",
        "topic": "2024"  # 您的PushPlus topic
    }
}
```
请自行修改文件中的相关路径和配置信息。例如，如果您希望配置文件路径为d:\桌面\config.json，请在`main.py`的第407行修改如下：
```python
config_path = Path("d:\\桌面\\config.json")  # 配置文件名称路径

### 3. 运行程序
在配置文件设置完成后，您可以直接运行`main.py`文件。程序会根据配置文件中的设置自动完成打卡任务。
```bash
python main.py
```

### 4. 更新Token
程序启动时会询问是否需要更新Token，输入`y`将强制更新所有用户的Token。您也可以根据需要手动更新Token。

## 注意事项
1. 请确保配置文件中的手机号和密码正确无误。
2. 使用PushPlus发送通知时，请确保PushPlus的Token和Topic正确配置。
   
## 免责声明
本项目仅用于学习和交流目的。使用本项目进行打卡时，请确保您已获得相关系统的授权，并遵守相关法律法规及公司政策。开发者不对使用本项目而导致的任何问题或后果负责。
