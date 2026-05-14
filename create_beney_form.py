#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【Beney】ギフティング案件 応募フォーム作成スクリプト
Google Forms API v1 + Google Drive API v3 を使用

【事前準備】
1. Google Cloud Console (https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成（または既存を選択）
3. 「APIとサービス」→「ライブラリ」で以下を有効化：
   - Google Forms API
   - Google Drive API
4. 「APIとサービス」→「認証情報」→「認証情報を作成」
   →「OAuthクライアントID」→「デスクトップアプリ」を選択
5. ダウンロードした JSON を credentials.json としてこのスクリプトと同じフォルダに配置
6. pip install -r requirements.txt を実行
7. python create_beney_form.py を実行（初回はブラウザが開いて認証を求められます）

【注意】
- 初回実行後は token.json が生成され、次回以降は自動認証されます
- token.json と credentials.json は絶対に公開しないでください
"""

import json
import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive',
]

FORM_TITLE = '【Beney】ギフティング案件 応募フォーム'
FORM_DESCRIPTION = (
    'このフォームはBeney公式ギフティング案件への応募フォームです。\n'
    '全ての同意事項にチェックいただいた方のみ、抽選対象となります。\n'
    '※本案件は抽選制です。当選を保証するものではありません。\n'
    '※商品お届け時の送料（実費）はご自身のご負担となります。'
)
FOLDER_NAME = 'Beney'


def get_credentials():
    """OAuth2認証でクレデンシャルを取得・更新"""
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print('ERROR: credentials.json が見つかりません。')
                print('Google Cloud Console で OAuth2 クライアントIDを作成し、')
                print('credentials.json としてこのスクリプトと同じフォルダに配置してください。')
                print('\nスクリプト冒頭のコメントに詳細な手順を記載しています。')
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return creds


def get_or_create_folder(drive_service, folder_name):
    """指定名のフォルダを検索し、なければ作成してIDを返す"""
    query = (
        f"name='{folder_name}' "
        "and mimeType='application/vnd.google-apps.folder' "
        "and trashed=false"
    )
    results = drive_service.files().list(
        q=query, fields='files(id, name)'
    ).execute()
    folders = results.get('files', [])

    if folders:
        folder_id = folders[0]['id']
        print(f'  既存の「{folder_name}」フォルダを使用: {folder_id}')
        return folder_id

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    folder = drive_service.files().create(
        body=folder_metadata, fields='id'
    ).execute()
    folder_id = folder['id']
    print(f'  「{folder_name}」フォルダを新規作成: {folder_id}')
    return folder_id


def move_file_to_folder(drive_service, file_id, folder_id):
    """ファイルを指定フォルダに移動（現在の親から切り離す）"""
    file = drive_service.files().get(
        fileId=file_id, fields='parents'
    ).execute()
    previous_parents = ','.join(file.get('parents', []))
    drive_service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents',
    ).execute()


def build_form_requests():
    """
    フォームの説明文更新 + 全設問の createItem リクエストを構築して返す。
    Items の順番はそのままフォームの表示順になる。
    """
    requests = []

    # フォーム説明文を設定
    requests.append({
        'updateFormInfo': {
            'info': {'description': FORM_DESCRIPTION},
            'updateMask': 'description',
        }
    })

    # フォームに追加するアイテムを順番に定義
    items = []

    # =========================================================
    # セクション1：基本情報
    # =========================================================
    items.append({
        'title': 'セクション1：基本情報',
        'description': 'お名前・連絡先・住所などの基本情報をご入力ください。',
        'pageBreakItem': {},
    })

    # Q1: お名前（本名）
    items.append({
        'title': 'Q1. お名前（本名）',
        'questionItem': {
            'question': {
                'required': True,
                'textQuestion': {'paragraph': False},
            }
        },
    })

    # Q2: メールアドレス
    # ※ Forms API v1 ではメール形式バリデーションのAPIサポートなし
    #   フォーム編集画面の「回答の検証」からメール形式を手動設定してください
    items.append({
        'title': 'Q2. メールアドレス',
        'questionItem': {
            'question': {
                'required': True,
                'textQuestion': {'paragraph': False},
            }
        },
    })

    # Q3: 性別
    items.append({
        'title': 'Q3. 性別',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'RADIO',
                    'options': [
                        {'value': '女性'},
                        {'value': '男性'},
                        {'value': '回答しない'},
                    ],
                },
            }
        },
    })

    # Q4: 生年月日
    items.append({
        'title': 'Q4. 生年月日',
        'description': '例）1995年4月1日',
        'questionItem': {
            'question': {
                'required': True,
                'textQuestion': {'paragraph': False},
            }
        },
    })

    # Q5: 郵便番号・住所（商品送付先）
    items.append({
        'title': 'Q5. 郵便番号・住所（商品送付先）',
        'description': '当選時の商品発送先になります。正確にご記入ください。',
        'questionItem': {
            'question': {
                'required': True,
                'textQuestion': {'paragraph': True},
            }
        },
    })

    # Q6: 電話番号
    items.append({
        'title': 'Q6. 電話番号',
        'questionItem': {
            'question': {
                'required': True,
                'textQuestion': {'paragraph': False},
            }
        },
    })

    # =========================================================
    # セクション2：SNS情報
    # =========================================================
    items.append({
        'title': 'セクション2：SNS情報',
        'description': 'ご利用のSNSアカウント情報をご入力ください。',
        'pageBreakItem': {},
    })

    # Q7: 主に使うSNS
    items.append({
        'title': 'Q7. 主に使うSNS',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [
                        {'value': 'Instagram'},
                        {'value': 'X（旧Twitter）'},
                        {'value': 'TikTok'},
                        {'value': 'YouTube'},
                        {'value': 'その他'},
                    ],
                },
            }
        },
    })

    # Q8: 各SNSのアカウントURL・ID
    items.append({
        'title': 'Q8. 各SNSのアカウントURL・ID',
        'description': '複数ある場合はすべてご記入ください。',
        'questionItem': {
            'question': {
                'required': False,
                'textQuestion': {'paragraph': True},
            }
        },
    })

    # Q9: Instagramのフォロワー数
    items.append({
        'title': 'Q9. Instagramのフォロワー数（おおよそ）',
        'questionItem': {
            'question': {
                'required': False,
                'choiceQuestion': {
                    'type': 'RADIO',
                    'options': [
                        {'value': '〜500'},
                        {'value': '500〜1,000'},
                        {'value': '1,000〜3,000'},
                        {'value': '3,000〜10,000'},
                        {'value': '10,000〜'},
                    ],
                },
            }
        },
    })

    # Q10: 普段投稿しているジャンル
    items.append({
        'title': 'Q10. 普段投稿しているジャンル',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [
                        {'value': 'コスメ・美容'},
                        {'value': 'ファッション'},
                        {'value': 'グルメ・料理'},
                        {'value': '育児・子育て'},
                        {'value': '暮らし・インテリア'},
                        {'value': 'フィットネス'},
                        {'value': 'その他'},
                    ],
                },
            }
        },
    })

    # Q11: 希望するギフティング案件のジャンル
    items.append({
        'title': 'Q11. 希望するギフティング案件のジャンル',
        'questionItem': {
            'question': {
                'required': False,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [
                        {'value': 'コスメ・スキンケア'},
                        {'value': 'ファッション'},
                        {'value': '食品・飲料'},
                        {'value': '育児用品'},
                        {'value': '生活雑貨'},
                        {'value': 'フィットネス用品'},
                        {'value': 'その他'},
                    ],
                },
            }
        },
    })

    # =========================================================
    # セクション3：今回の案件内容（固定テキスト表示）
    # 案件ごとにこのセクションの説明文を差し替えて使用してください
    # =========================================================
    items.append({
        'title': 'セクション3：今回の案件内容',
        'description': (
            '以下の案件詳細をご確認ください。\n'
            '案件ごとにこのセクションの内容を差し替えてご使用ください。\n\n'
            '・案件名：【案件名をここに記入】\n'
            '・商品参考価格：【価格をここに記入】\n'
            '・投稿期限：商品到着後14日以内\n'
            '・投稿先SNS：Instagram フィード投稿必須'
        ),
        'pageBreakItem': {},
    })

    # 案件詳細テキストアイテム（説明用の非回答フィールド）
    items.append({
        'title': '案件詳細について',
        'description': (
            '上記のセクション説明に記載の案件詳細をご確認のうえ、次のセクションの同意事項にお進みください。\n'
            '※このフォームを複製して使用する場合は、セクション3の説明文を案件ごとに更新してください。'
        ),
        'textItem': {},
    })

    # =========================================================
    # セクション4：同意事項
    # 各項目は1択チェックボックス＋必須設定で「全員チェック必須」を実現
    # =========================================================
    items.append({
        'title': 'セクション4：同意事項',
        'description': '以下の全ての項目にチェックを入れた方のみ、応募完了となります。',
        'pageBreakItem': {},
    })

    # Q16: 送料負担への同意
    items.append({
        'title': 'Q16. 送料負担への同意',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [{
                        'value': (
                            '商品お届け時の送料（実費）はご自身のご負担となります。'
                            'ご同意いただけない場合は応募をご遠慮ください。'
                        )
                    }],
                },
            }
        },
    })

    # Q17: 投稿義務への同意
    items.append({
        'title': 'Q17. 投稿義務への同意',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [{
                        'value': (
                            '商品受領後、指定期限内にSNSへの投稿が完了しない場合、'
                            '今後のギフティング案件への参加をお断りする場合があります。'
                        )
                    }],
                },
            }
        },
    })

    # Q18: 投稿証明の提出への同意
    items.append({
        'title': 'Q18. 投稿証明の提出への同意',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [{
                        'value': (
                            '投稿完了後、投稿のURLまたはスクリーンショットを'
                            'Beney公式LINEへ送付いただきます。'
                        )
                    }],
                },
            }
        },
    })

    # Q19: PR表記義務への同意
    items.append({
        'title': 'Q19. PR表記義務への同意',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [{
                        'value': (
                            '景品表示法・ステルスマーケティング規制に基づき、'
                            '投稿には必ず #PR または #ギフティング の表記が必要です。'
                            'これに違反した場合、ポイント付与の対象外となる場合があります。'
                        )
                    }],
                },
            }
        },
    })

    # Q20: 抽選制であることへの同意
    items.append({
        'title': 'Q20. 抽選制であることへの同意',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [{
                        'value': (
                            '本案件は応募者の中から抽選で当選者を決定します。'
                            '必ずしも当選を保証するものではありません。'
                        )
                    }],
                },
            }
        },
    })

    # Q21: 2次利用への同意
    items.append({
        'title': 'Q21. 2次利用への同意',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [{
                        'value': (
                            '投稿いただいたコンテンツをBeney・案件企業のプロモーション素材として'
                            '使用する場合があります。'
                        )
                    }],
                },
            }
        },
    })

    # Q22: 個人情報取り扱いへの同意
    items.append({
        'title': 'Q22. 個人情報取り扱いへの同意',
        'questionItem': {
            'question': {
                'required': True,
                'choiceQuestion': {
                    'type': 'CHECKBOX',
                    'options': [{
                        'value': (
                            '入力いただいた個人情報はギフティング案件の運営目的にのみ使用し、'
                            '第三者への提供は行いません。'
                        )
                    }],
                },
            }
        },
    })

    # =========================================================
    # セクション5：その他
    # =========================================================
    items.append({
        'title': 'セクション5：その他',
        'description': '任意記入欄です。ご自由にお書きください。',
        'pageBreakItem': {},
    })

    # Q23: アレルギー・使用できない成分など
    items.append({
        'title': 'Q23. アレルギー・使用できない成分など',
        'questionItem': {
            'question': {
                'required': False,
                'textQuestion': {'paragraph': True},
            }
        },
    })

    # Q24: ギフティング案件への要望・希望
    items.append({
        'title': 'Q24. ギフティング案件への要望・希望',
        'questionItem': {
            'question': {
                'required': False,
                'textQuestion': {'paragraph': True},
            }
        },
    })

    # Q25: その他、運営への連絡事項
    items.append({
        'title': 'Q25. その他、運営への連絡事項',
        'questionItem': {
            'question': {
                'required': False,
                'textQuestion': {'paragraph': True},
            }
        },
    })

    # createItem リクエストをインデックス付きで構築
    for i, item in enumerate(items):
        requests.append({
            'createItem': {
                'item': item,
                'location': {'index': i},
            }
        })

    return requests


def create_response_spreadsheet(drive_service, form_title, folder_id):
    """回答収集用スプレッドシートをBeneyフォルダ内に作成"""
    spreadsheet_metadata = {
        'name': f'{form_title}（回答）',
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [folder_id],
    }
    spreadsheet = drive_service.files().create(
        body=spreadsheet_metadata,
        fields='id, webViewLink',
    ).execute()
    return spreadsheet['id'], spreadsheet['webViewLink']


def main():
    print('=' * 60)
    print('【Beney】ギフティング案件 応募フォーム作成スクリプト')
    print('=' * 60)
    print()

    # OAuth2認証
    print('[1/5] Google OAuth2認証中...')
    try:
        creds = get_credentials()
        print('      認証成功')
    except Exception as e:
        print(f'      認証エラー: {e}')
        sys.exit(1)

    # APIサービスの初期化
    forms_service = build('forms', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # フォームの作成（タイトルのみ）
    print(f'[2/5] フォームを作成中: {FORM_TITLE}')
    try:
        result = forms_service.forms().create(body={
            'info': {
                'title': FORM_TITLE,
                'documentTitle': FORM_TITLE,
            }
        }).execute()
        form_id = result['formId']
        responder_uri = result['responderUri']
        print(f'      フォームID: {form_id}')
    except HttpError as e:
        print(f'      フォーム作成エラー: {e}')
        sys.exit(1)

    # 設問・セクションを batchUpdate で一括追加
    print('[3/5] 設問・セクションを追加中...')
    try:
        requests = build_form_requests()
        forms_service.forms().batchUpdate(
            formId=form_id,
            body={'requests': requests},
        ).execute()
        item_count = sum(1 for r in requests if 'createItem' in r)
        print(f'      {item_count} 件のアイテムを追加しました')
    except HttpError as e:
        print(f'      設問追加エラー: {e}')
        sys.exit(1)

    # Beneyフォルダの取得または作成
    print(f'[4/5] 「{FOLDER_NAME}」フォルダを確認中...')
    try:
        folder_id = get_or_create_folder(drive_service, FOLDER_NAME)
        move_file_to_folder(drive_service, form_id, folder_id)
        print(f'      フォームをフォルダに移動しました')
    except HttpError as e:
        print(f'      フォルダ操作エラー: {e}')
        sys.exit(1)

    # 回答スプレッドシートの作成
    print('[5/5] 回答スプレッドシートを作成中...')
    try:
        spreadsheet_id, spreadsheet_url = create_response_spreadsheet(
            drive_service, FORM_TITLE, folder_id
        )
        print(f'      スプレッドシートID: {spreadsheet_id}')
    except HttpError as e:
        print(f'      スプレッドシート作成エラー: {e}')
        sys.exit(1)

    # URL の組み立て
    edit_url = f'https://docs.google.com/forms/d/{form_id}/edit'
    folder_url = f'https://drive.google.com/drive/folders/{folder_id}'
    spreadsheet_edit_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit'

    # 結果の表示
    print()
    print('=' * 60)
    print('フォーム作成完了！')
    print('=' * 60)
    print()
    print('【フォーム回答URL（応募者向け）】')
    print(f'  {responder_uri}')
    print()
    print('【フォーム編集URL（管理者向け）】')
    print(f'  {edit_url}')
    print()
    print('【回答スプレッドシートURL】')
    print(f'  {spreadsheet_edit_url}')
    print()
    print('【BeneyフォルダURL】')
    print(f'  {folder_url}')
    print()
    print('-' * 60)
    print('【次の手動作業】')
    print('回答スプレッドシートとフォームを連携するには:')
    print('  1. フォーム編集URLを開く')
    print('  2.「回答」タブをクリック')
    print('  3. スプレッドシートアイコン（緑色）をクリック')
    print('  4.「既存のスプレッドシートを選択」を選ぶ')
    print('  5. 上記スプレッドシートを選択して「選択」をクリック')
    print()
    print('Q2（メールアドレス）のバリデーション設定:')
    print('  1. フォーム編集URLを開く')
    print('  2. Q2の設問右下「・・・」→「回答の検証」')
    print('  3.「テキスト」→「メールアドレス」を選択')
    print('-' * 60)

    # 結果を JSON ファイルに保存
    output = {
        'form_id': form_id,
        'form_responder_url': responder_uri,
        'form_edit_url': edit_url,
        'spreadsheet_id': spreadsheet_id,
        'spreadsheet_url': spreadsheet_edit_url,
        'folder_id': folder_id,
        'folder_url': folder_url,
    }
    with open('form_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print('結果を form_result.json に保存しました。')
    print('=' * 60)


if __name__ == '__main__':
    main()
