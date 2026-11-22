export function escapeHtml(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, function (character) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character];
  });
}

export function formatBytes(value) {
  if (value === null || value === undefined || value === '') return 'Unknown';
  var number = Number(value);
  if (!isFinite(number) || number < 0) return 'Unknown';
  var units = ['B', 'KB', 'MB', 'GB', 'TB'];
  var index = 0;
  while (number >= 1024 && index < units.length - 1) {
    number /= 1024;
    index += 1;
  }
  var digits = index === 0 ? 0 : number >= 100 ? 0 : number >= 10 ? 1 : 2;
  return number.toFixed(digits) + ' ' + units[index];
}

export function display(value, fallback) {
  return value === null || value === undefined || value === '' ? (fallback || 'Unknown') : String(value);
}

export function csrfToken() {
  var parts = document.cookie ? document.cookie.split(';') : [];
  for (var index = 0; index < parts.length; index += 1) {
    var part = parts[index].trim();
    if (part.indexOf('csrftoken=') === 0) return decodeURIComponent(part.slice('csrftoken='.length));
  }
  return '';
}

export function headers() {
  return {
    Accept: 'application/json',
    'X-CSRFToken': csrfToken(),
    'X-Requested-With': 'XMLHttpRequest'
  };
}

export async function getJSON(url) {
  var response = await fetch(url, { credentials: 'same-origin', headers: headers() });
  var data;
  try { data = await response.json(); } catch (error) { throw new Error('HTTP ' + response.status); }
  if (!response.ok) throw new Error(display(data && data.error, 'Request failed (' + response.status + ').'));
  return data;
}

export async function postForm(url, fields) {
  var form = new FormData();
  Object.keys(fields || {}).forEach(function (key) { form.append(key, fields[key]); });
  var response = await fetch(url, { method: 'POST', credentials: 'same-origin', headers: headers(), body: form });
  var data;
  try { data = await response.json(); } catch (error) { throw new Error('HTTP ' + response.status); }
  if (!response.ok) throw new Error(display(data && data.error, 'Request failed (' + response.status + ').'));
  return data;
}

export function uploadFile(url, file, mode, onProgress) {
  return new Promise(function (resolve, reject) {
    var request = new XMLHttpRequest();
    var form = new FormData();
    form.append('file', file);
    form.append('execution_mode', mode);
    request.open('POST', url, true);
    Object.keys(headers()).forEach(function (key) { request.setRequestHeader(key, headers()[key]); });
    request.upload.onprogress = function (event) {
      if (event.lengthComputable) onProgress(Math.round(event.loaded / event.total * 100));
    };
    request.onload = function () {
      var data;
      try { data = JSON.parse(request.responseText); } catch (error) { reject(new Error('Upload response was not JSON.')); return; }
      if (!data || !data.success) {
        reject(new Error(display(data && data.error, 'Upload failed (HTTP ' + request.status + ').')));
        return;
      }
      resolve(data);
    };
    request.onerror = function () { reject(new Error('Upload request failed.')); };
    request.send(form);
  });
}
