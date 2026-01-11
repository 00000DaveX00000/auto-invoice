# 出纳发票识别系统 - 全栈 Demo 设计

## 技术栈
- **前端**: Vue 3 + Ant Design Vue + TypeScript + Vite
- **后端**: FastAPI + Python 3.11+ (uv 管理虚拟环境)
- **数据库**: SQLite (通过 SQLAlchemy)
- **AI**: 智谱 GLM-4.6V 多模态模型
- **包管理**: uv (后端) + pnpm/npm (前端)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue 3)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ 发票上传  │  │ 识别结果  │  │ 汇总统计  │  │Excel导出│  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP API
┌─────────────────────────▼───────────────────────────────┐
│                   后端 (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ 上传API   │  │ 识别服务  │  │ 分类引擎  │  │导出服务 │  │
│  └──────────┘  └────┬─────┘  └──────────┘  └─────────┘  │
│                     │                                    │
│              ┌──────▼──────┐                             │
│              │ GLM-4.6V API │                            │
│              └─────────────┘                             │
└─────────────────────────┬───────────────────────────────┘
                          │
                   ┌──────▼──────┐
                   │   SQLite    │
                   └─────────────┘
```

---

## 项目目录结构

```
出纳/
├── backend/
│   ├── pyproject.toml           # uv 项目配置
│   ├── uv.lock                  # uv 锁定文件
│   ├── .python-version          # Python 版本
│   ├── .env                     # 环境变量 (API Key)
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI 入口
│       ├── config.py            # 配置管理
│       ├── database.py          # 数据库连接
│       ├── models/
│       │   ├── __init__.py
│       │   └── invoice.py       # 发票数据模型
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── invoice.py       # Pydantic 模型
│       ├── services/
│       │   ├── __init__.py
│       │   ├── glm_service.py   # GLM-4.6V 调用
│       │   ├── invoice_parser.py # 发票解析
│       │   ├── voucher_service.py # 凭证生成
│       │   └── excel_export.py  # Excel 导出
│       └── routers/
│           ├── __init__.py
│           └── invoice.py       # 发票相关 API
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── api/
│   │   │   └── invoice.ts       # API 调用封装
│   │   ├── components/
│   │   │   ├── InvoiceUpload.vue    # 上传组件
│   │   │   ├── InvoiceTable.vue     # 结果列表
│   │   │   ├── SummaryPanel.vue     # 汇总面板
│   │   │   └── AnomalyList.vue      # 异常清单
│   │   ├── views/
│   │   │   └── Home.vue
│   │   ├── types/
│   │   │   └── invoice.ts       # TypeScript 类型定义
│   │   └── stores/
│   │       └── invoice.ts       # Pinia 状态管理
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
└── design.md                    # 原设计文档
```

---

## 数据模型设计

### Invoice (发票表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| invoice_no | String | 发票号码 |
| invoice_date | Date | 开票日期 |
| invoice_type | String | 类型 (专票/普票/电子) |
| seller_name | String | 销方名称 |
| seller_tax_no | String | 销方税号 |
| amount | Decimal | 金额 |
| tax_amount | Decimal | 税额 |
| total_amount | Decimal | 价税合计 |
| expense_category | String | 费用科目 |
| reimbursement_person | String | 报销人 |
| confidence | Float | 识别置信度 (0-1) |
| anomaly_flag | String | 异常标记 |
| anomaly_reason | String | 异常原因 |
| image_path | String | 原图路径 |
| raw_response | JSON | GLM 原始返回 |
| created_at | DateTime | 创建时间 |

### Voucher (凭证表) - 可导入金蝶/用友
| 字段 | 类型 | 说明 |
|------|------|------|
| 编制日期 | Date | 凭证日期 |
| 凭证类型 | String | 转/收/付 |
| 凭证序号 | Int | 序号 |
| 凭证号 | String | 凭证编号 |
| 制单人 | String | 操作员 |
| 附件张数 | Int | 发票数量 |
| 会计年度 | String | YYYYMM |
| 科目编码 | String | 如 6602 (管理费用) |
| 科目名称 | String | 如 管理费用-差旅费 |
| 凭证摘要 | String | 报销说明 |
| 借贷方向 | String | 借/贷 |
| 金额 | Decimal | 金额 |
| 币种 | String | 人民币 |
| 汇率 | Decimal | 1 |
| 员工姓名 | String | 报销人 |
| 往来单位名称 | String | 销方名称 |
| 部门名称 | String | 报销部门 |

---

## API 设计

### 1. 上传发票
```
POST /api/invoices/upload
Content-Type: multipart/form-data
Body: files[] (多文件)
Response: { task_id, total_count }
```

### 2. 获取识别结果
```
GET /api/invoices?page=1&size=20&category=差旅费
Response: { items: Invoice[], total, summary }
```

### 3. 获取汇总统计
```
GET /api/invoices/summary
Response: {
  by_category: [{ category, count, amount, tax }],
  total_count, total_amount, total_tax,
  anomaly_count
}
```

### 4. 导出 Excel
```
GET /api/invoices/export
Response: Excel 文件 (4个Sheet)
  - Sheet1: 发票明细表
  - Sheet2: 费用汇总表
  - Sheet3: 异常清单
  - Sheet4: 凭证导入模板 (金蝶/用友格式)
```

### 5. 生成凭证
```
POST /api/vouchers/generate
Body: { invoice_ids[], voucher_date, voucher_type, maker }
Response: { vouchers: Voucher[] }
```

### 6. 更新发票 (人工修正)
```
PATCH /api/invoices/{id}
Body: { expense_category, anomaly_flag, ... }
```

---

## 核心逻辑

### GLM-4.6V 调用 Prompt
```python
INVOICE_PROMPT = """
请识别这张发票图片，提取以下信息并以 JSON 格式返回：
{
  "invoice_no": "发票号码",
  "invoice_date": "开票日期 (YYYY-MM-DD)",
  "invoice_type": "增值税专票/增值税普票/电子普票/其他",
  "seller_name": "销方名称",
  "seller_tax_no": "销方税号",
  "amount": 金额(数字),
  "tax_amount": 税额(数字),
  "total_amount": 价税合计(数字),
  "items": ["商品/服务名称列表"],
  "confidence": 置信度(0-1)
}

如果某个字段无法识别，请设为 null。
"""
```

### 费用科目自动映射规则
```python
CATEGORY_RULES = {
    "交通费": ["滴滴", "出租", "地铁", "公交", "高铁", "火车", "机票", "航空"],
    "差旅费-住宿": ["酒店", "宾馆", "民宿", "住宿"],
    "业务招待费": ["餐饮", "餐厅", "饭店", "酒楼"],
    "办公费": ["文具", "打印", "复印", "办公用品"],
    "通讯费": ["电信", "移动", "联通", "话费"],
}
```

### 异常检测规则
1. **金额异常**: 单张 > 5000 元标记复核
2. **置信度低**: < 0.9 进入人工复核
3. **日期异常**: 超过 180 天的发票
4. **连号检测**: 同一销方连续发票号

### 科目编码映射 (可配置)
```python
ACCOUNT_CODE_MAP = {
    "交通费": {"code": "660206", "name": "管理费用-交通费"},
    "差旅费-住宿": {"code": "660207", "name": "管理费用-差旅费"},
    "业务招待费": {"code": "660208", "name": "管理费用-业务招待费"},
    "办公费": {"code": "660201", "name": "管理费用-办公费"},
    "通讯费": {"code": "660203", "name": "管理费用-通讯费"},
}
```

### 凭证生成逻辑
```
1. 按费用科目分组发票
2. 每组生成一条借方分录 (费用科目)
3. 生成对应贷方分录 (其他应付款/银行存款)
4. 自动计算附件张数
5. 生成凭证摘要: "报销{员工姓名}{月份}{科目}费用"
```

---

## 前端页面设计

### 主界面布局
```
┌─────────────────────────────────────────────────────────────┐
│  出纳发票识别系统              [生成凭证] [导出Excel]        │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │     拖拽上传发票图片 或 点击选择文件                   │  │
│  │         支持 JPG/PNG/PDF，最多 200 张                  │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ 全部 │ │交通费│ │差旅费│ │招待费│ │ 异常 │              │
│  │ 156  │ │  45  │ │  38  │ │  12  │ │  5   │              │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘              │
├─────────────────────────────────────────────────────────────┤
│  ☑ 发票号    日期      销方      金额   税额  科目    状态  │
│  ─────────────────────────────────────────────────────────  │
│  ☑ 012345 2025-01-08 滴滴出行  85.00   0    交通费    ✓    │
│  ☑ 012346 2025-01-09 全聚德   680.00   0    招待费    ⚠️   │
│  ...                                                        │
├─────────────────────────────────────────────────────────────┤
│  汇总: 已选 15 张 | 合计 ¥12,580.00 | 税额 ¥680.00          │
└─────────────────────────────────────────────────────────────┘
```

### 凭证预览弹窗
```
┌─────────────────────────────────────────────────────────────┐
│  生成凭证预览                                      [确认]   │
├─────────────────────────────────────────────────────────────┤
│  编制日期: [2025-01-10]  凭证类型: [转账凭证 ▼]  制单人: DY │
├─────────────────────────────────────────────────────────────┤
│  科目编码   科目名称          摘要           借方     贷方  │
│  ─────────────────────────────────────────────────────────  │
│  660206   管理费用-交通费   报销1月交通费   850.00         │
│  660207   管理费用-差旅费   报销1月住宿费  1200.00         │
│  660208   管理费用-招待费   报销1月招待费   680.00         │
│  2241     其他应付款-员工                         2730.00  │
│  ─────────────────────────────────────────────────────────  │
│  合计                                    2730.00  2730.00  │
└─────────────────────────────────────────────────────────────┘
```

---

## 实现步骤

### Phase 1: 后端基础
1. 初始化后端项目
   ```bash
   cd 出纳 && mkdir backend && cd backend
   uv init --name invoice-backend
   uv add fastapi uvicorn sqlalchemy python-multipart aiofiles
   uv add zhipuai openpyxl python-dotenv
   ```
2. 配置 SQLite + SQLAlchemy
3. 创建发票数据模型
4. 实现文件上传 API

### Phase 2: AI 集成
5. 封装 GLM-4.6V 调用服务
6. 实现发票解析逻辑
7. 添加费用科目自动分类
8. 实现异常检测规则

### Phase 3: 后端完善
9. 实现查询和统计 API
10. 实现凭证生成服务 (voucher_service.py)
11. 实现 Excel 导出 (含凭证导入模板)
12. 添加批量处理和并发控制

### Phase 4: 前端开发
13. 初始化前端项目
    ```bash
    cd 出纳
    npm create vite@latest frontend -- --template vue-ts
    cd frontend
    npm install
    npm install ant-design-vue @ant-design/icons-vue
    npm install axios pinia
    ```
14. 配置 Ant Design Vue
15. 实现上传组件 (InvoiceUpload.vue)
16. 实现结果列表 (InvoiceTable.vue)
17. 实现凭证预览弹窗 (VoucherModal.vue)
18. 实现 Excel 下载

### Phase 5: 联调测试
19. 配置 Vite 代理，前后端联调
20. 测试批量上传和凭证生成
21. 验证导出的 Excel 可导入金蝶

### 启动命令
```bash
# 后端 (端口 8000)
cd backend && uv run uvicorn app.main:app --reload

# 前端 (端口 5173)
cd frontend && npm run dev
```

---

## 验证方案

1. **后端 API 测试**: 使用 FastAPI 自带的 `/docs` Swagger UI
2. **上传测试**: 准备 5-10 张测试发票图片
3. **识别准确性**: 对比 GLM 返回与实际发票信息
4. **导出验证**: 检查生成的 Excel 格式和数据完整性
5. **批量测试**: 模拟 50+ 张发票的批量处理

---

## 关键文件清单

| 文件 | 作用 |
|------|------|
| `backend/app/main.py` | FastAPI 应用入口 |
| `backend/app/services/glm_service.py` | GLM-4.6V 调用核心 |
| `backend/app/services/invoice_parser.py` | 发票解析和分类 |
| `backend/app/services/voucher_service.py` | 凭证生成逻辑 |
| `backend/app/services/excel_export.py` | Excel 导出 (含凭证模板) |
| `frontend/src/components/InvoiceUpload.vue` | 上传组件 |
| `frontend/src/components/InvoiceTable.vue` | 结果列表 |
| `frontend/src/components/VoucherModal.vue` | 凭证预览弹窗 |
