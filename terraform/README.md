# Terraform Modules - Plug & Play

Drop your Terraform code here and it just works!

## Quick Start

### 1. Create your module folder

```bash
mkdir terraform/my-app
```

### 2. Add your Terraform files

```
terraform/
└── my-app/
    ├── main.tf           # Your resources
    ├── variables.tf      # Input variables (match catalog params)
    └── outputs.tf        # Outputs shown to users (optional)
```

### 3. Create a catalog entry

Create `catalog/my-app.yaml`:

```yaml
id: my-app
name: My Application
description: Deploys my application infrastructure
category: development
skill_level: beginner
estimated_monthly_cost_usd: 50-100

parameters:
  - name: project_name
    label: Project Name
    type: string
    required: true

  - name: environment
    label: Environment
    type: select
    options: [dev, test, prod]
    default: dev

  - name: region
    label: Azure Region
    type: select
    options: [eastus, westus2, northeurope]
    default: eastus

  - name: size
    label: Size
    type: select
    options: [small, medium, large]
    default: small

ado_pipeline:
  project: YourProject
  pipeline_id: 123          # Your generic pipeline ID
  branch: main
  extra_params:             # Pass module name to generic pipeline
    module_name: my-app
```

### 4. Done!

Restart the portal and your new template appears in the catalog.

---

## How It Works

```
User fills form in Portal
        │
        ▼
Portal triggers ADO Pipeline with parameters:
  - module_name: "my-app"
  - project_name: "user-input"
  - environment: "dev"
  - etc.
        │
        ▼
Generic Pipeline runs:
  cd terraform/my-app
  terraform init
  terraform plan -var="project_name=..." -var="environment=..."
  terraform apply
        │
        ▼
Resources deployed!
```

---

## Variable Mapping

Your `variables.tf` should match catalog `parameters`:

**catalog/my-app.yaml:**
```yaml
parameters:
  - name: project_name      # ← This name
    label: Project Name
    type: string
```

**terraform/my-app/variables.tf:**
```hcl
variable "project_name" {   # ← Must match
  type = string
}
```

---

## Standard Variables

These are passed automatically if defined in your module:

| Variable | Description | Example |
|----------|-------------|---------|
| `project_name` | User's project name | `my-project` |
| `environment` | Target environment | `dev`, `test`, `prod` |
| `region` | Azure region | `eastus` |
| `size` | T-shirt size | `small`, `medium`, `large` |

---

## Example Structure

```
terraform/
├── _example/              # Reference implementation
│   ├── main.tf
│   └── variables.tf
├── my-app/                # Your first module
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── data-platform/         # Another module
│   ├── main.tf
│   ├── variables.tf
│   ├── storage.tf
│   └── databricks.tf
└── README.md              # This file
```

---

## Tips

1. **Use the example**: Copy `_example/` as a starting point
2. **Validate locally**: Run `terraform validate` before pushing
3. **Test variables**: Ensure all required vars have defaults or are in catalog
4. **Outputs**: Define outputs for info users need post-deployment
5. **Naming**: Use `var.project_name` and `var.environment` in resource names to avoid conflicts
