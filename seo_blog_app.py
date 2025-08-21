import streamlit as st
import os
import requests
import json
from datetime import datetime
import time

# ページ設定
st.set_page_config(
    page_title="SEOブログ記事生成アプリ",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Claude API関数
def generate_article_with_claude(theme_keyword, target_audience, article_purpose, article_length, additional_notes=""):
    """Claude APIを使って記事を生成する"""
    api_key = os.environ.get("CLAUDE_API_KEY")
    
    if not api_key:
        return None, "APIキーが設定されていません"
    
    # プロンプト作成
    prompt = create_article_prompt(theme_keyword, target_audience, article_purpose, article_length, additional_notes)
    
    # 試行するモデルのリスト（優先順位順）
    models_to_try = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-haiku-20240307"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    # 各モデルを順番に試行
    for model in models_to_try:
        try:
            data = {
                "model": model,
                "max_tokens": 4000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                article_content = result["content"][0]["text"]
                return article_content, None
            elif response.status_code == 401:
                return None, "APIキーが無効です。正しいAPIキーを入力してください。"
            elif response.status_code == 429:
                return None, "API利用制限に達しました。しばらく待ってから再試行してください。"
            elif response.status_code == 404:
                # このモデルが利用できない場合は次のモデルを試行
                continue
            else:
                try:
                    error_detail = response.json()
                    error_msg = f"API Error: {response.status_code} - {error_detail.get('error', {}).get('message', 'Unknown error')}"
                except:
                    error_msg = f"API Error: {response.status_code} - {response.text}"
                return None, error_msg
                
        except requests.exceptions.RequestException as e:
            continue  # ネットワークエラーの場合は次のモデルを試行
        except Exception as e:
            continue  # その他のエラーの場合も次のモデルを試行
    
    # 全てのモデルで失敗した場合
    return None, "利用可能なClaudeモデルが見つかりません。APIキーまたはアカウントの設定を確認してください。"

def create_article_prompt(theme_keyword, target_audience, article_purpose, article_length, additional_notes):
    """記事生成用のプロンプトを作成"""
    
    purpose_map = {
        "集客・アクセスアップ": "検索エンジンからの集客を目的とし、SEOを意識した内容",
        "商品・サービス紹介": "商品やサービスの魅力を伝え、購買につなげる内容",
        "知識・ノウハウ共有": "読者に有用な知識やノウハウを提供する教育的な内容",
        "ブランディング": "企業や個人のブランド価値を高める内容",
        "問題解決・FAQ": "読者の悩みや疑問を解決する実用的な内容",
        "その他": "読者に価値を提供する質の高い内容"
    }
    
    prompt = f"""
あなたは優秀なSEOライターです。以下の条件に基づいて、高品質なブログ記事を作成してください。

## 記事の条件
- **テーマ・キーワード**: {theme_keyword}
- **想定読者**: {target_audience}
- **記事の目的**: {purpose_map.get(article_purpose, article_purpose)}
- **文字数**: 約{article_length}文字
- **追加要望**: {additional_notes if additional_notes else "特になし"}

## 記事の構成要件
1. **タイトル**: SEOを意識した魅力的なタイトル
2. **導入文**: 読者の興味を引く導入部分
3. **見出し構造**: H2、H3を使った階層的な構成
4. **本文**: 実用的で価値のある内容
5. **まとめ**: 記事の要点を整理した結論

## 執筆の指針
- 読者にとって価値のある実用的な情報を提供
- SEOを意識したキーワードの自然な配置
- 読みやすい文章構成と適切な改行
- 具体例や体験談を交えた親しみやすい内容
- 信頼性の高い情報と正確性の確保

記事を**Markdown形式**で出力してください。
"""
    
    return prompt
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        margin-bottom: 2rem;
    }
    .step-header {
        background: linear-gradient(90deg, #2E86AB, #A23B72);
        color: white;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background: #E8F4FD;
        padding: 1rem;
        border-left: 4px solid #2E86AB;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .generated-article {
        background: #F8F9FA;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #DEE2E6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'article_history' not in st.session_state:
    st.session_state.article_history = []

def main():
    # メインヘッダー
    st.markdown("<h1 class='main-header'>📝 SEOブログ記事生成アプリ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>簡単な入力だけで高品質なSEO記事を自動生成</p>", unsafe_allow_html=True)
    
    # サイドバー - 使い方ガイド
    with st.sidebar:
        st.header("📚 使い方ガイド")
        st.markdown("""
        **Step 1**: 記事のテーマやキーワードを入力
        
        **Step 2**: 想定読者層を選択
        
        **Step 3**: 記事の目的を選択
        
        **Step 4**: 記事の長さを指定
        
        **Step 5**: 生成ボタンをクリック
        """)
        
        st.header("⚙️ 設定")
        # API設定
        api_key_input = st.text_input("Claude API Key", type="password", help="Claude APIキーを入力してください")
        
        if api_key_input:
            os.environ["CLAUDE_API_KEY"] = api_key_input
            st.success("APIキーが設定されました")
        
        # 記事履歴
        st.header("📚 記事履歴")
        if 'article_history' not in st.session_state:
            st.session_state.article_history = []
        
        if st.session_state.article_history:
            for i, history_item in enumerate(reversed(st.session_state.article_history)):
                with st.expander(f"📄 {history_item['theme_keyword'][:20]}..."):
                    st.write(f"**生成日時:** {history_item['generated_at']}")
                    st.write(f"**文字数:** {history_item['article_length']:,}文字")
                    if st.button(f"復元", key=f"restore_{i}"):
                        st.session_state.generated_article = history_item['article_content']
                        st.session_state.article_metadata = {k: v for k, v in history_item.items() if k != 'article_content'}
                        st.success("記事が復元されました!")
                        st.rerun()
        else:
            st.write("生成された記事はまだありません")
    
    # メインコンテンツエリア
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<h2 class='step-header'>📝 記事情報入力</h2>", unsafe_allow_html=True)
        
        # 入力フォーム
        with st.form("article_form"):
            # サンプルデータがある場合の初期値設定
            sample = st.session_state.get('sample_data', {})
            
            # Step 1: テーマ・キーワード
            st.subheader("1️⃣ 記事のテーマ・キーワード")
            theme_keyword = st.text_area(
                "記事で扱いたいテーマやキーワードを入力してください",
                placeholder="例: Python プログラミング 初心者向け",
                height=100,
                value=sample.get('theme_keyword', '')
            )
            
            # Step 2: 想定読者層
            st.subheader("2️⃣ 想定読者層")
            audience_options = [
                "初心者・未経験者",
                "中級者・経験者", 
                "専門家・エキスパート",
                "一般消費者",
                "企業担当者",
                "その他"
            ]
            default_audience = sample.get('target_audience', audience_options[0])
            audience_index = audience_options.index(default_audience) if default_audience in audience_options else 0
            
            target_audience = st.selectbox(
                "記事を読む人はどのような方ですか？",
                audience_options,
                index=audience_index
            )
            
            if target_audience == "その他":
                custom_audience = st.text_input("具体的な読者層を教えてください")
            
            # Step 3: 記事の目的
            st.subheader("3️⃣ 記事の目的")
            purpose_options = [
                "集客・アクセスアップ",
                "商品・サービス紹介",
                "知識・ノウハウ共有",
                "ブランディング", 
                "問題解決・FAQ",
                "その他"
            ]
            default_purpose = sample.get('article_purpose', purpose_options[0])
            purpose_index = purpose_options.index(default_purpose) if default_purpose in purpose_options else 0
            
            article_purpose = st.selectbox(
                "この記事の目的は何ですか？",
                purpose_options,
                index=purpose_index
            )
            
            # Step 4: 記事の長さ
            st.subheader("4️⃣ 記事の長さ")
            length_options = [1000, 1500, 2000, 2500, 3000, 4000, 5000]
            default_length = sample.get('article_length', 2000)
            length_index = length_options.index(default_length) if default_length in length_options else 2
            
            article_length = st.select_slider(
                "希望する文字数を選択してください",
                options=length_options,
                value=length_options[length_index],
                format_func=lambda x: f"{x:,}文字"
            )
            
            # Step 5: 追加情報（任意）
            st.subheader("5️⃣ 追加情報（任意）")
            additional_notes = st.text_area(
                "書きたい内容のメモや特別な要望があれば入力してください",
                placeholder="例: 実際の体験談を含めたい、図表を使って説明したい など",
                height=80,
                value=sample.get('additional_notes', '')
            )
            
            # 生成ボタン
            submitted = st.form_submit_button(
                "🚀 記事を生成する",
                use_container_width=True,
                type="primary"
            )
            
            # デモ用サンプル入力ボタン
            if st.form_submit_button("📝 サンプル入力", use_container_width=True):
                st.session_state.sample_data = {
                    "theme_keyword": "Python プログラミング 初心者",
                    "target_audience": "初心者・未経験者",
                    "article_purpose": "知識・ノウハウ共有",
                    "article_length": 2000,
                    "additional_notes": "実際のコード例を含めて、分かりやすく説明したい"
                }
                st.rerun()
    
    with col2:
        st.markdown("<h2 class='step-header'>📄 プレビュー・結果</h2>", unsafe_allow_html=True)
        
        if submitted:
            # 入力値の検証
            validation_errors = validate_inputs(theme_keyword, target_audience, article_purpose)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            elif not os.environ.get("CLAUDE_API_KEY"):
                st.error("サイドバーでClaude API Keyを設定してください")
            else:
                # 入力値のサニタイズ
                clean_theme = sanitize_input(theme_keyword)
                clean_notes = sanitize_input(additional_notes)
                
                # 進捗表示
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # 記事生成開始
                    status_text.text("🤖 AIが記事を生成しています...")
                    progress_bar.progress(25)
                    
                    # Claude APIで記事生成
                    article_content, error = generate_article_with_claude(
                        clean_theme, 
                        target_audience, 
                        article_purpose, 
                        article_length, 
                        clean_notes
                    )
                    
                    progress_bar.progress(75)
                    
                    if error:
                        st.error(f"記事生成でエラーが発生しました: {error}")
                        progress_bar.empty()
                        status_text.empty()
                    else:
                        progress_bar.progress(100)
                        status_text.text("✅ 記事生成完了!")
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        
                        # セッション状態に記事を保存
                        st.session_state.generated_article = article_content
                        st.session_state.article_metadata = {
                            "theme_keyword": clean_theme,
                            "target_audience": target_audience,
                            "article_purpose": article_purpose,
                            "article_length": article_length,
                            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # 記事履歴に追加
                        add_to_history(article_content, st.session_state.article_metadata)
                        
                        st.success("記事が生成されました!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"予期しないエラーが発生しました: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
        
        # 生成された記事の表示
        if hasattr(st.session_state, 'generated_article'):
            display_generated_article()
            
        elif not submitted:
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.markdown("**👈 左側のフォームに必要な情報を入力して、記事を生成してください**")
            st.markdown("</div>", unsafe_allow_html=True)

def display_generated_article():
    """生成された記事を表示する"""
    if not hasattr(st.session_state, 'generated_article'):
        return
    
    # 記事情報
    metadata = st.session_state.article_metadata
    
    # 記事表示エリア
    st.markdown("### 📄 生成された記事")
    
    # タブで表示切り替え
    tab1, tab2, tab3 = st.tabs(["📖 プレビュー", "📝 編集", "💾 ダウンロード"])
    
    with tab1:
        # プレビュー表示
        st.markdown("<div class='generated-article'>", unsafe_allow_html=True)
        st.markdown(st.session_state.generated_article)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 記事情報
        with st.expander("📊 記事情報"):
            st.write(f"**テーマ・キーワード:** {metadata['theme_keyword']}")
            st.write(f"**想定読者:** {metadata['target_audience']}")
            st.write(f"**記事の目的:** {metadata['article_purpose']}")
            st.write(f"**文字数:** {metadata['article_length']:,}文字目安")
            st.write(f"**生成日時:** {metadata['generated_at']}")
    
    with tab2:
        # 編集機能
        st.markdown("**記事を編集できます（変更は一時的です）:**")
        edited_article = st.text_area(
            "記事内容",
            value=st.session_state.generated_article,
            height=400,
            label_visibility="collapsed"
        )
        
        if st.button("💾 変更を保存", type="secondary"):
            st.session_state.generated_article = edited_article
            st.success("変更が保存されました!")
            st.rerun()
        
        if st.button("🔄 記事を再生成", type="primary"):
            # 現在のメタデータを使って再生成
            with st.spinner("記事を再生成しています..."):
                metadata = st.session_state.article_metadata
                article_content, error = generate_article_with_claude(
                    metadata['theme_keyword'], 
                    metadata['target_audience'], 
                    metadata['article_purpose'], 
                    metadata['article_length']
                )
                
                if error:
                    st.error(f"再生成でエラーが発生しました: {error}")
                else:
                    st.session_state.generated_article = article_content
                    add_to_history(article_content, metadata)
                    st.success("記事が再生成されました!")
                    st.rerun()
    
    with tab3:
        # ダウンロード機能
        st.markdown("**記事をダウンロードできます:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # テキスト形式ダウンロード
            st.download_button(
                label="📄 テキスト形式でダウンロード",
                data=st.session_state.generated_article,
                file_name=f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            # Markdown形式ダウンロード
            st.download_button(
                label="📝 Markdown形式でダウンロード",
                data=st.session_state.generated_article,
                file_name=f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        
        # 記事統計とSEO分析
        try:
            article_stats = analyze_article(st.session_state.generated_article)
            st.markdown("**📊 記事統計とSEO分析:**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("文字数", f"{article_stats['char_count']:,}")
            with col2:
                st.metric("段落数", article_stats['paragraph_count'])
            with col3:
                st.metric("見出し数", article_stats['heading_count'])
            with col4:
                st.metric("推定読了時間", f"{article_stats['reading_time']}分")
            
            # SEO分析結果
            if 'theme_keyword' in st.session_state.article_metadata:
                seo_analysis = analyze_seo_elements(
                    st.session_state.generated_article, 
                    st.session_state.article_metadata['theme_keyword']
                )
                
                st.markdown("**🔍 SEO分析結果:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**キーワード出現回数:** {seo_analysis['keyword_count']}回")
                    st.write(f"**キーワード密度:** {seo_analysis['keyword_density']:.1f}%")
                    
                with col2:
                    st.write(f"**見出しにキーワード含有:** {'✅' if seo_analysis['keyword_in_headings'] else '❌'}")
                    st.write(f"**適切な文字数:** {'✅' if seo_analysis['appropriate_length'] else '❌'}")
            else:
                st.warning("SEO分析には記事のメタデータが必要です")
                
        except Exception as e:
            st.error(f"記事分析でエラーが発生しました: {str(e)}")
            st.write("記事は正常に生成されましたが、統計分析が実行できませんでした。")

def validate_inputs(theme_keyword, target_audience, article_purpose):
    """入力値を検証"""
    errors = []
    
    # テーマ・キーワードの検証
    if not theme_keyword or len(theme_keyword.strip()) < 3:
        errors.append("テーマ・キーワードは3文字以上で入力してください")
    
    if len(theme_keyword) > 200:
        errors.append("テーマ・キーワードは200文字以内で入力してください")
    
    # 読者層の検証
    if not target_audience:
        errors.append("想定読者層を選択してください")
    
    # 記事目的の検証
    if not article_purpose:
        errors.append("記事の目的を選択してください")
    
    return errors

def sanitize_input(text):
    """入力テキストをサニタイズ"""
    if not text:
        return ""
    
    # 危険な文字列を除去
    dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
    cleaned = text
    
    for pattern in dangerous_patterns:
        cleaned = cleaned.replace(pattern, '')
    
    return cleaned.strip()
    """SEO要素を分析"""
    # 基本統計
    total_chars = len(article_content)
    words = article_content.split()
    
    # キーワード分析
    keyword_count = article_content.lower().count(main_keyword.lower())
    keyword_density = (keyword_count / len(words)) * 100 if words else 0
    
    # 見出し分析
    headings = [line for line in article_content.split('\n') if line.strip().startswith('#')]
    keyword_in_headings = any(main_keyword.lower() in heading.lower() for heading in headings)
    
    # 文字数判定（1500-4000文字が理想的）
    appropriate_length = 1500 <= total_chars <= 4000
    
    return {
        'keyword_count': keyword_count,
        'keyword_density': keyword_density,
        'keyword_in_headings': keyword_in_headings,
        'appropriate_length': appropriate_length
    }

def add_to_history(article_content, metadata):
    """記事を履歴に追加"""
    if 'article_history' not in st.session_state:
        st.session_state.article_history = []
    
    history_item = {
        "article_content": article_content,
        **metadata
    }
    
    # 最新を先頭に追加し、10件まで保持
    st.session_state.article_history.insert(0, history_item)
    if len(st.session_state.article_history) > 10:
        st.session_state.article_history = st.session_state.article_history[:10]

def analyze_article(article_content):
    """記事の統計情報を分析"""
    char_count = len(article_content)
    paragraph_count = len([p for p in article_content.split('\n') if p.strip()])
    heading_count = len([line for line in article_content.split('\n') if line.strip().startswith('#')])
    
    # 読了時間の推定（日本語：400文字/分）
    reading_time = max(1, char_count // 400)
    
    return {
        'char_count': char_count,
        'paragraph_count': paragraph_count,
        'heading_count': heading_count,
        'reading_time': reading_time
    }

def analyze_seo_elements(article_content, main_keyword):
    """SEO要素を分析"""
    # 基本統計
    total_chars = len(article_content)
    words = article_content.split()
    
    # キーワード分析
    keyword_count = article_content.lower().count(main_keyword.lower())
    keyword_density = (keyword_count / len(words)) * 100 if words else 0
    
    # 見出し分析
    headings = [line for line in article_content.split('\n') if line.strip().startswith('#')]
    keyword_in_headings = any(main_keyword.lower() in heading.lower() for heading in headings)
    
    # 文字数判定（1500-4000文字が理想的）
    appropriate_length = 1500 <= total_chars <= 4000
    
    return {
        'keyword_count': keyword_count,
        'keyword_density': keyword_density,
        'keyword_in_headings': keyword_in_headings,
        'appropriate_length': appropriate_length
    }

if __name__ == "__main__":
    main()
