gemini_api_key = "선생님의_제미나이_API_키"

[google_drive]
service_account_json = """
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  ... (구글 서비스 계정 JSON 파일의 전체 내용을 따옴표 사이에 넣어주세요)
}
"""
