# 窩福社區 Home Assistant 自訂整合元件

[![hacs_badge](https://img.shields.io/badge/HACS-custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![GitHub release (latest version)](https://img.shields.io/github/v/release/osk2/wafflecity-custom-component?style=for-the-badge)
[![GitHub license](https://img.shields.io/github/license/osk2/wafflecity-custom-component?style=for-the-badge)](https://github.com/osk2/wafflecity-custom-component/blob/master/LICENSE)

[English](README.md) | **繁體中文**

窩福社區（Waffle City）包裹追蹤的 Home Assistant 整合元件。

## 功能

- 追蹤社區待領包裹
- 每 15 分鐘自動更新
- 包裹詳細資訊以感測器屬性呈現

## 安裝

### HACS（推薦）

1. 在 Home Assistant 中開啟 HACS
2. 點選「整合」
3. 點選右上角選單，選擇「自訂存放庫」
4. 新增 `https://github.com/osk2/wafflecity-custom-component`，類別選擇「Integration」
5. 搜尋「Waffle City」並安裝
6. 重新啟動 Home Assistant

### 手動安裝

1. 將 `custom_components/wafflecity` 資料夾複製到 Home Assistant 的 `custom_components` 目錄
2. 重新啟動 Home Assistant

## 設定

1. 前往**設定** > **裝置與服務**
2. 點選**新增整合**
3. 搜尋「Waffle City」
4. 輸入您的帳號資訊：
   - **手機號碼**：您註冊的手機號碼
   - **密碼**：您的帳號密碼
   - **國碼**：選擇您的國家（預設：TW）

## 感測器

整合元件會建立感測器 `sensor.waffle_city_pending_packages`，包含：

- **狀態**：待領包裹數量
- **屬性**：
  - `packages`：包裹詳細資訊列表
  - `user_id`：您的窩福社區使用者 ID

## 自動化範例

```yaml
automation:
  - alias: "新包裹通知"
    trigger:
      - platform: state
        entity_id: sensor.waffle_city_pending_packages
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
    action:
      - service: notify.mobile_app
        data:
          title: "新包裹已送達"
          message: "您有 {{ states('sensor.waffle_city_pending_packages') }} 件包裹待領取"
```

## 支援國家

TW, CN, HK, MO, JP, KR, TH, SG, MY, ID, VN, PH, AU, IN

## 授權條款

MIT
