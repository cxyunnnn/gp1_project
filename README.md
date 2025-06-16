gp1_project
這是一個新聞處理平台
專案功能介紹：
1.中英文翻譯 2.情感分析 3.文字語音朗讀 4.重整欄

使用方式
https://www.canva.com/design/DAGpYwlnDDs/dyJ3uFUQPQPw-Dq-Yc7bUQ/watch?utm_content=DAGpYwlnDDs&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h13c04eca6f

建立 Docker 映像
docker image build -t gp1:latest .

查看映像
docker image ls

執行容器
docker container run -d --name gp1 -p 8080:8080 gp1:latest

設定參數（可自訂）
RESOURCE_GROUP="your-resource-group" ACR_NAME="youracrname" CONTAINER_NAME="gp1-container" REGION="eastasia"

登入 Azure
建立資源群組
az group create --name $RESOURCE_GROUP --location $REGION

建立 Azure Container Registry（ACR）
az acr create --resource-group $RESOURCE_GROUP
--name $ACR_NAME
--sku Basic
--admin-enabled true

登入 ACR
docker login $ACR_NAME.azurecr.io $ACR_NAME $ACR_PASSWORD

查看目前的 Docker 映像列表
docker image ls

建構映像（請將 $ACR_NAME 替換為你自己的 ACR 名稱）
docker image build -t $ACR_NAME.azurecr.io/vision:latest .

推送映像到 ACR（需先 az acr login）
docker push $ACR_NAME.azurecr.io/vision:latest

#建立容器執行個體並開放8080port

訪問8080port
