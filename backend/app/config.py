import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "PayPulse - Enterprise Salary & Payroll Management"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "paypulse_super_secret_jwt_key_99384729103847291")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database (SQLite by default, easily overridden by postgresql:// in env)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./salary_manager.db")
    
    # Company details for payslips & reports
    COMPANY_NAME: str = "Apex Technologies & Global Solutions Pvt Ltd"
    COMPANY_ADDRESS: str = "Level 8, Cyber Horizon Tech Park, Silicon Corridor, Bengaluru, KA 560103"
    COMPANY_PHONE: str = "+91 80 4920 8800"
    COMPANY_EMAIL: str = "payroll@apextechglobal.com"
    COMPANY_WEBSITE: str = "www.apextechglobal.com"
    COMPANY_PAN: str = "AAACA9823L"
    COMPANY_TAN: str = "BLRA12345C"
    COMPANY_CIN: str = "U72200KA2018PTC112345"
    
    # Standard statutory defaults (India & Global standard compliance)
    EPF_EMPLOYEE_PERCENT: float = 12.0
    EPF_EMPLOYER_PERCENT: float = 12.0
    EPF_WAGE_CEILING: float = 15000.0
    ESI_EMPLOYEE_PERCENT: float = 0.75
    ESI_EMPLOYER_PERCENT: float = 3.25
    ESI_WAGE_CEILING: float = 21000.0
    STANDARD_PTAX: float = 200.0
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
