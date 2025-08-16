# agente
Purpose - Dissertation

This includes the code of AgentE and the testing scripts as well.

To run, hit the following commmands each in different terminal

uvicorn server.mcp_host:app --host 0.0.0.0 --port 8000

uvicorn server.crew_host:app --host 0.0.0.0 --port 8001

uvicorn server.backend_job_host:app --host 0.0.0.0 --port 8002

streamlit run streamlit/app.py

mlflow run
