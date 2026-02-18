from flask import Flask, render_template, request, jsonify
import akshare as ak
import pandas as pd
import requests
import datetime
import os

app = Flask(__name__)

DEBUG_MODE = False
PORT = int(os.environ.get("PORT", 8080))

# 你的 API Key 我已经直接填在这里
DOUBAO_API_KEY = "6fd21b6a-281f-4fea-9886-cdf961e5c738"

def get_a_stock_simple_data():
    try:
        # 适配akshare新版本，增加超时容错
        df = ak.stock_zh_a_spot_em(timeout=10).head(30)
        core_columns = ['代码', '名称', '最新价', '涨跌幅', '涨跌额', '换手率']
        df = df[core_columns].fillna(0)
        return df
    except Exception as e:
        print("获取数据失败，使用测试数据")
        test_data = {
            '代码': ['600519', '000858', '601318', '000001', '600036'],
            '名称': ['贵州茅台', '五粮液', '中国平安', '平安银行', '招商银行'],
            '最新价': [1800.00, 80.00, 40.00, 15.00, 35.00],
            '涨跌幅': [1.2, -0.5, 0.8, 0.3, -0.2],
            '涨跌额': [21.6, -0.4, 0.32, 0.045, -0.07],
            '换手率': [0.1, 0.3, 0.2, 0.5, 0.15]
        }
        return pd.DataFrame(test_data)

def get_stock_rank():
    df = get_a_stock_simple_data()
    rank_df = df.sort_values(by='涨跌幅', ascending=False).head(10)
    return rank_df.to_dict('records')

def get_stock_analysis():
    df = get_a_stock_simple_data()
    up_stocks = df[df['涨跌幅'] > 0.5].head(5)
    down_stocks = df[df['涨跌幅'] < -0.5].head(5)
    return {
        "up": up_stocks.to_dict('records'),
        "down": down_stocks.to_dict('records')
    }

def ai_chat(question):
    api_key = DOUBAO_API_KEY
    if not api_key:
        return "请配置API Key"

    prompt = f"""
你是A股数据科普助手，只回答数据问题，不提供任何买入/卖出建议，不预测股价。
必须在结尾加：本回答仅数据科普，不构成投资建议，投资有风险。

问题：{question}
"""
    try:
        response = requests.post(
            "https://api.doubao.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "doubao-pro",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"AI暂时无法回答：{str(e)}，本回答仅数据科普，不构成投资建议，投资有风险。"

@app.route('/')
def index():
    rank_list = get_stock_rank()
    analysis_data = get_stock_analysis()
    return render_template('index.html', rank=rank_list, analysis=analysis_data)

@app.route('/chat', methods=['POST'])
def chat():
    question = request.json.get('question', '')
    answer = ai_chat(question)
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG_MODE)
