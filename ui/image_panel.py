import streamlit as st
import base64
import os

def render_image_panel():
    with st.expander("📸 Upload Crop Image for GPT-4o Vision Analysis", expanded=False):
        ci, cp = st.columns([2, 1])
        with ci:
            uploaded = st.file_uploader(
                "Drop your crop photo here",
                type=["jpg","jpeg","png","webp"],
                label_visibility="collapsed"
            )
            img_q = st.text_input(
                "Question about image",
                placeholder="What disease is on my wheat? / میری گندم میں کیا ہے؟"
            )
            analyze_btn = st.button("🔍 Analyze with GPT-4o", disabled=(uploaded is None))

            if analyze_btn and uploaded:
                with st.spinner("🤖 GPT-4o Vision analyzing..."):
                    try:
                        from openai import OpenAI
                        client   = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                        img_b64  = base64.b64encode(uploaded.read()).decode()
                        question = img_q or "Diagnose this crop and provide precise treatment advice."
                        resp     = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": question},
                                    {"type": "image_url", "image_url": {
                                        "url": f"data:image/jpeg;base64,{img_b64}",
                                        "detail": "high"
                                    }}
                                ]
                            }],
                            max_tokens=700, temperature=0.15
                        )
                        st.session_state["img_context"] = resp.choices[0].message.content
                        st.success("✅ Analyzed! Send a message to get agent advice based on this image.")
                    except Exception as e:
                        import logging
                        logging.error(f"Vision error: {e}")
                        st.error(f"Vision error: {e}")

        with cp:
            if uploaded:
                st.image(uploaded, caption="Crop image", use_container_width=True)
            if st.session_state.get("img_context"):
                st.markdown("**📋 Vision Result:**")
                st.markdown(
                    f"<div class='ib'>{st.session_state['img_context'][:300]}...</div>",
                    unsafe_allow_html=True
                )
