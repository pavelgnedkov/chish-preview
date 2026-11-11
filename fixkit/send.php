<?php
// Приём заявок с форм сайта chish.ru (вместо Contact Form 7). Письмо уходит на адрес школы.
header('Content-Type: application/json; charset=utf-8');
$TO = 'chish.school@gmail.com';
function out($ok, $err = '') { echo json_encode(['ok' => $ok, 'error' => $err], JSON_UNESCAPED_UNICODE); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') out(false, 'Метод не поддерживается');
if (!empty($_POST['website'])) out(true); // ловушка для ботов
$text = trim((string)($_POST['text'] ?? ''));
$page = substr(preg_replace('~[^\w/\-]~u', '', (string)($_POST['page'] ?? '/')), 0, 200);
if ($text === '' || mb_strlen($text) > 5000) out(false, 'Заполните форму');
if (preg_match_all('~https?://~i', $text) > 3) out(false, 'Слишком много ссылок');
// не больше 5 писем в час с одного IP
$ip = $_SERVER['HTTP_X_REAL_IP'] ?? $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0';
$f = sys_get_temp_dir() . '/chish_send_' . md5($ip);
$hits = array_filter(array_map('intval', @file($f) ?: []), fn($t) => $t > time() - 3600);
if (count($hits) >= 5) out(false, 'Слишком много сообщений, попробуйте позже');
$hits[] = time(); @file_put_contents($f, implode("\n", $hits));
$body = "Сообщение с сайта chish.ru (страница: $page)\n\n$text\n\n---\nIP: $ip\nВремя: " . date('d.m.Y H:i');
$subj = '=?UTF-8?B?' . base64_encode('Заявка с сайта chish.ru') . '?=';
$headers = "From: chish.ru <noreply@chish.ru>\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit";
out(@mail($TO, $subj, $body, $headers) ? true : false, 'Не удалось отправить, позвоните нам: 8 (8442) 711-738');
