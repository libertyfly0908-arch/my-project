/**
 * 【Beney】ギフティング案件 応募フォーム作成スクリプト
 * Google Apps Script 版
 *
 * 使い方:
 *   1. script.google.com で新しいプロジェクトを作成
 *   2. このコードを貼り付け
 *   3. 上部メニューの「実行」→「createBeneyForm」を選択
 *   4. 初回は権限許可のダイアログが出るので「許可」をクリック
 *   5. 完了後、ログにURLが表示されます
 */

function createBeneyForm() {

  // =========================================================
  // フォームの作成
  // =========================================================
  var form = FormApp.create('【Beney】ギフティング案件 応募フォーム');

  form.setDescription(
    'このフォームはBeney公式ギフティング案件への応募フォームです。\n' +
    '全ての同意事項にチェックいただいた方のみ、抽選対象となります。\n' +
    '※本案件は抽選制です。当選を保証するものではありません。\n' +
    '※商品お届け時の送料（実費）はご自身のご負担となります。'
  );

  // フォームの設定
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false);
  form.setShowLinkToRespondAgain(false);
  form.setProgressBar(true);  // セクションのプログレスバーを表示

  // =========================================================
  // セクション1：基本情報
  // =========================================================
  form.addPageBreakItem()
    .setTitle('セクション1：基本情報')
    .setHelpText('お名前・連絡先・住所などの基本情報をご入力ください。');

  // Q1: お名前
  form.addTextItem()
    .setTitle('Q1. お名前（本名）')
    .setRequired(true);

  // Q2: メールアドレス（メール形式バリデーション付き）
  var emailItem = form.addTextItem()
    .setTitle('Q2. メールアドレス')
    .setRequired(true);
  var emailValidation = FormApp.createTextValidation()
    .requireTextIsEmail()
    .build();
  emailItem.setValidation(emailValidation);

  // Q3: 性別
  form.addMultipleChoiceItem()
    .setTitle('Q3. 性別')
    .setChoiceValues(['女性', '男性', '回答しない'])
    .setRequired(true);

  // Q4: 生年月日
  form.addTextItem()
    .setTitle('Q4. 生年月日')
    .setHelpText('例）1995年4月1日')
    .setRequired(true);

  // Q5: 郵便番号・住所
  form.addParagraphTextItem()
    .setTitle('Q5. 郵便番号・住所（商品送付先）')
    .setHelpText('当選時の商品発送先になります。正確にご記入ください。')
    .setRequired(true);

  // Q6: 電話番号
  form.addTextItem()
    .setTitle('Q6. 電話番号')
    .setRequired(true);

  // =========================================================
  // セクション2：SNS情報
  // =========================================================
  form.addPageBreakItem()
    .setTitle('セクション2：SNS情報')
    .setHelpText('ご利用のSNSアカウント情報をご入力ください。');

  // Q7: 主に使うSNS
  form.addCheckboxItem()
    .setTitle('Q7. 主に使うSNS')
    .setChoiceValues(['Instagram', 'X（旧Twitter）', 'TikTok', 'YouTube', 'その他'])
    .setRequired(true);

  // Q8: 各SNSのアカウントURL・ID
  form.addParagraphTextItem()
    .setTitle('Q8. 各SNSのアカウントURL・ID')
    .setHelpText('複数ある場合はすべてご記入ください。')
    .setRequired(false);

  // Q9: Instagramのフォロワー数
  form.addMultipleChoiceItem()
    .setTitle('Q9. Instagramのフォロワー数（おおよそ）')
    .setChoiceValues(['〜500', '500〜1,000', '1,000〜3,000', '3,000〜10,000', '10,000〜'])
    .setRequired(false);

  // Q10: 普段投稿しているジャンル
  form.addCheckboxItem()
    .setTitle('Q10. 普段投稿しているジャンル')
    .setChoiceValues(['コスメ・美容', 'ファッション', 'グルメ・料理', '育児・子育て', '暮らし・インテリア', 'フィットネス', 'その他'])
    .setRequired(true);

  // Q11: 希望するギフティング案件のジャンル
  form.addCheckboxItem()
    .setTitle('Q11. 希望するギフティング案件のジャンル')
    .setChoiceValues(['コスメ・スキンケア', 'ファッション', '食品・飲料', '育児用品', '生活雑貨', 'フィットネス用品', 'その他'])
    .setRequired(false);

  // =========================================================
  // セクション3：今回の案件内容（固定テキスト表示）
  // 案件ごとにこのセクションの説明文を差し替えて使用
  // =========================================================
  form.addPageBreakItem()
    .setTitle('セクション3：今回の案件内容')
    .setHelpText(
      '以下の案件詳細をご確認ください。\n' +
      '案件ごとにこのセクションの内容を差し替えてご使用ください。\n\n' +
      '・案件名：【案件名をここに記入】\n' +
      '・商品参考価格：【価格をここに記入】\n' +
      '・投稿期限：商品到着後14日以内\n' +
      '・投稿先SNS：Instagram フィード投稿必須'
    );

  // 案件詳細の説明テキスト
  form.addSectionHeaderItem()
    .setTitle('案件詳細について')
    .setHelpText(
      '上記のセクション説明に記載の案件詳細をご確認ください。\n' +
      'このフォームを複製して使用する場合は、セクション3の説明文を案件ごとに更新してください。'
    );

  // =========================================================
  // セクション4：同意事項
  // 各項目：1択チェックボックス＋必須 → 全員チェック必須を実現
  // =========================================================
  form.addPageBreakItem()
    .setTitle('セクション4：同意事項')
    .setHelpText('以下の全ての項目にチェックを入れた方のみ、応募完了となります。');

  // Q16: 送料負担への同意
  form.addCheckboxItem()
    .setTitle('Q16. 送料負担への同意')
    .setChoiceValues([
      '商品お届け時の送料（実費）はご自身のご負担となります。ご同意いただけない場合は応募をご遠慮ください。'
    ])
    .setRequired(true);

  // Q17: 投稿義務への同意
  form.addCheckboxItem()
    .setTitle('Q17. 投稿義務への同意')
    .setChoiceValues([
      '商品受領後、指定期限内にSNSへの投稿が完了しない場合、今後のギフティング案件への参加をお断りする場合があります。'
    ])
    .setRequired(true);

  // Q18: 投稿証明の提出への同意
  form.addCheckboxItem()
    .setTitle('Q18. 投稿証明の提出への同意')
    .setChoiceValues([
      '投稿完了後、投稿のURLまたはスクリーンショットをBeney公式LINEへ送付いただきます。'
    ])
    .setRequired(true);

  // Q19: PR表記義務への同意
  form.addCheckboxItem()
    .setTitle('Q19. PR表記義務への同意')
    .setChoiceValues([
      '景品表示法・ステルスマーケティング規制に基づき、投稿には必ず #PR または #ギフティング の表記が必要です。これに違反した場合、ポイント付与の対象外となる場合があります。'
    ])
    .setRequired(true);

  // Q20: 抽選制であることへの同意
  form.addCheckboxItem()
    .setTitle('Q20. 抽選制であることへの同意')
    .setChoiceValues([
      '本案件は応募者の中から抽選で当選者を決定します。必ずしも当選を保証するものではありません。'
    ])
    .setRequired(true);

  // Q21: 2次利用への同意
  form.addCheckboxItem()
    .setTitle('Q21. 2次利用への同意')
    .setChoiceValues([
      '投稿いただいたコンテンツをBeney・案件企業のプロモーション素材として使用する場合があります。'
    ])
    .setRequired(true);

  // Q22: 個人情報取り扱いへの同意
  form.addCheckboxItem()
    .setTitle('Q22. 個人情報取り扱いへの同意')
    .setChoiceValues([
      '入力いただいた個人情報はギフティング案件の運営目的にのみ使用し、第三者への提供は行いません。'
    ])
    .setRequired(true);

  // =========================================================
  // セクション5：その他
  // =========================================================
  form.addPageBreakItem()
    .setTitle('セクション5：その他')
    .setHelpText('任意記入欄です。ご自由にお書きください。');

  // Q23: アレルギー・使用できない成分など
  form.addParagraphTextItem()
    .setTitle('Q23. アレルギー・使用できない成分など')
    .setRequired(false);

  // Q24: ギフティング案件への要望・希望
  form.addParagraphTextItem()
    .setTitle('Q24. ギフティング案件への要望・希望')
    .setRequired(false);

  // Q25: その他、運営への連絡事項
  form.addParagraphTextItem()
    .setTitle('Q25. その他、運営への連絡事項')
    .setRequired(false);

  // =========================================================
  // Beneyフォルダへの移動
  // =========================================================
  var folderId = getOrCreateBeneyFolder_();
  var formFile = DriveApp.getFileById(form.getId());
  var beneyFolder = DriveApp.getFolderById(folderId);

  // フォームをBeneyフォルダに追加
  beneyFolder.addFile(formFile);
  // マイドライブのルートから削除
  DriveApp.getRootFolder().removeFile(formFile);

  // =========================================================
  // 回答スプレッドシートの作成・連携
  // =========================================================
  var spreadsheet = SpreadsheetApp.create('【Beney】ギフティング案件 応募フォーム（回答）');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, spreadsheet.getId());

  // スプレッドシートもBeneyフォルダに移動
  var ssFile = DriveApp.getFileById(spreadsheet.getId());
  beneyFolder.addFile(ssFile);
  DriveApp.getRootFolder().removeFile(ssFile);

  // =========================================================
  // 結果をログに出力
  // =========================================================
  var formUrl     = form.getPublishedUrl();
  var editUrl     = form.getEditUrl();
  var folderUrl   = 'https://drive.google.com/drive/folders/' + folderId;
  var ssUrl       = spreadsheet.getUrl();

  Logger.log('========================================');
  Logger.log('フォーム作成完了！');
  Logger.log('========================================');
  Logger.log('【フォーム回答URL（応募者向け）】');
  Logger.log(formUrl);
  Logger.log('【フォーム編集URL（管理者向け）】');
  Logger.log(editUrl);
  Logger.log('【回答スプレッドシートURL】');
  Logger.log(ssUrl);
  Logger.log('【BeneyフォルダURL】');
  Logger.log(folderUrl);
  Logger.log('========================================');

  // 完了ダイアログを表示
  var ui = SpreadsheetApp.getUi ? SpreadsheetApp.getUi() : null;
  var message =
    'フォーム作成完了！\n\n' +
    '回答URL:\n' + formUrl + '\n\n' +
    '編集URL:\n' + editUrl + '\n\n' +
    '※「表示」→「ログ」でURLを確認できます。';

  // ログでURLを確認できるようにポップアップも試みる
  try {
    Browser.msgBox('【Beney】フォーム作成完了', message, Browser.Buttons.OK);
  } catch (e) {
    // スプレッドシートUIなしで実行された場合はログのみ
    Logger.log('完了。上記URLをご確認ください。');
  }
}

/**
 * Beneyフォルダを検索し、なければ作成してフォルダIDを返す
 */
function getOrCreateBeneyFolder_() {
  var folders = DriveApp.getFoldersByName('Beney');
  if (folders.hasNext()) {
    var folder = folders.next();
    Logger.log('既存のBeneyフォルダを使用: ' + folder.getId());
    return folder.getId();
  }
  var newFolder = DriveApp.createFolder('Beney');
  Logger.log('Beneyフォルダを新規作成: ' + newFolder.getId());
  return newFolder.getId();
}
