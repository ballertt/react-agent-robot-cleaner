import time

import streamlit as st
from agent.react_agent import ReactAgent

# 标题
st.title("智扫通机器人智能客服")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "message" not in st.session_state:
    st.session_state["message"] = []
#页面一刷新，整个代码都会从头到尾跑一遍，为了保证以前的对话效果都在页面中展示
#在每一次页面重新启动的时候，都要把message从历史记录里取出来，然后在页面全写出去
for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 用户输入提示词
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_messages = []
    with st.spinner("智能客服思考中..."):
        res_stream = st.session_state["agent"].execute_stream(prompt)    #拿到迭代器对象
        #不能用st.chat_message().write_stream(res_stream)，因为我们也想要agent回答的内容页保存在
        #历史信息里呈现出来，但是res_stream是迭代器对象，用完一次就完了，用不了第二次
        #后续的st.session_state["message"].append({"role": "assistant", "content": res_stream})
        #里面的res_stream是没有内容的
        #这时候要添加一个中间的方法把迭代器里的内容捕获出来
        def capture(generator, cache_list):

            for chunk in generator:
                cache_list.append(chunk)

                for char in chunk:
                    time.sleep(0.01)
                    yield char
        #本质上传入一个迭代器，再返回这个迭代器出去，只是中间把迭代器里的内容
        #往一个叫缓存的列表里面放
        st.chat_message("assistant").write(capture(res_stream, response_messages))
        st.session_state["message"].append({"role": "assistant", "content": response_messages[-1]})
        #只记录最后一条（ai真正返回的是最后一条，其他大多是中间进程）
        st.rerun()