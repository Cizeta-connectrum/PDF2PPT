/**
 * PDF2PPT dashboard backend.
 *
 * Bind this script to a Google Sheet (Extensions > Apps Script), set the
 * script property API_TOKEN (Project Settings > Script Properties), then
 * deploy as a Web App (Deploy > New deployment > Web app):
 *   - Execute as: Me
 *   - Who has access: Anyone
 * Copy the resulting /exec URL into GAS_WEBAPP_URL, and the same token
 * value into GAS_API_TOKEN, on the PDF2PPT server.
 */

const SHEET_NAME = 'Apps';
const HEADERS = ['id', 'name', 'url', 'created_at'];

function getSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(HEADERS);
  }
  return sheet;
}

function isAuthorized_(token) {
  const expected = PropertiesService.getScriptProperties().getProperty('API_TOKEN');
  return !!expected && token === expected;
}

function jsonResponse_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  if (!isAuthorized_(e.parameter.token)) {
    return jsonResponse_({ error: 'unauthorized' });
  }

  const sheet = getSheet_();
  const rows = sheet.getDataRange().getValues();
  const apps = [];
  for (let i = 1; i < rows.length; i++) {
    const [id, name, url, createdAt] = rows[i];
    if (!id) continue;
    apps.push({ id: String(id), name, url, created_at: createdAt });
  }
  return jsonResponse_(apps);
}

function doPost(e) {
  let body;
  try {
    body = JSON.parse(e.postData.contents || '{}');
  } catch (err) {
    return jsonResponse_({ error: 'invalid_json' });
  }

  if (!isAuthorized_(body.token)) {
    return jsonResponse_({ error: 'unauthorized' });
  }

  const sheet = getSheet_();

  if (body.action === 'add') {
    const name = String(body.name || '').trim();
    const url = String(body.url || '').trim();
    if (!name || !url) {
      return jsonResponse_({ error: 'name and url are required' });
    }
    const id = Utilities.getUuid().replace(/-/g, '');
    const createdAt = new Date().toISOString();
    sheet.appendRow([id, name, url, createdAt]);
    return jsonResponse_({ id, name, url, created_at: createdAt });
  }

  if (body.action === 'delete') {
    const rows = sheet.getDataRange().getValues();
    for (let i = 1; i < rows.length; i++) {
      if (String(rows[i][0]) === String(body.id)) {
        sheet.deleteRow(i + 1);
        return jsonResponse_({ success: true });
      }
    }
    return jsonResponse_({ success: false, error: 'not_found' });
  }

  return jsonResponse_({ error: 'invalid_action' });
}
