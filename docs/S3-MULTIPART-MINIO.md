# S3 Multipart Upload voi MinIO

## Vai tro trong project

Flow chinh cua project nam trong `Server/api/upload_video/routes.py`:

1. `POST /upload-video/init`
2. Client upload tung part truc tiep len MinIO bang presigned URL.
3. `POST /upload-video/complete`
4. Backend goi `complete_multipart_upload`.
5. Backend tao record `Media` voi `status = PENDING`.

Cach nay tot hon upload chunk qua backend vi backend khong phai nhan toan bo bytes video. Backend chi cap quyen va ghi metadata.

## Multipart upload la gi

Multipart upload la co che cua S3 cho phep mot object duoc upload bang nhieu part doc lap. S3/MinIO se giu cac part tam thoi theo `UploadId`. Khi client upload xong tat ca part, backend gui danh sach `PartNumber` va `ETag` de S3 ghep thanh object cuoi cung.

```text
Backend create_multipart_upload
  -> S3 tra UploadId
  -> Backend tao presigned URL cho tung PartNumber
  -> Client PUT tung part len URL
  -> S3 tra ETag tung part
  -> Client gui UploadId + danh sach ETag ve backend
  -> Backend complete_multipart_upload
```

## Vi sao can presigned URL

Presigned URL la URL tam thoi da duoc ky san. Client co the upload truc tiep len S3/MinIO ma khong can biet access key/secret key.

Trong project:

```python
url = s3_client.generate_presigned_url(
    ClientMethod="upload_part",
    Params={
        "Bucket": settings.bucket,
        "Key": filename,
        "UploadId": upload_id,
        "PartNumber": i,
    },
    ExpiresIn=900,
)
```

`ExpiresIn=900` nghia la URL het han sau 15 phut. Neu upload file lon hon thoi gian nay, client can xin lai URL hoac backend can thiet ke co che refresh.

## ETag dung de lam gi

Moi lan upload part thanh cong, S3/MinIO tra ve header `ETag`. Khi complete, backend phai gui dung cap:

```json
[
  { "PartNumber": 1, "ETag": "\"etag-part-1\"" },
  { "PartNumber": 2, "ETag": "\"etag-part-2\"" }
]
```

Neu sai ETag, thieu part, hoac part number khong dung, `complete_multipart_upload` se fail.

## Nhung diem can canh giac trong code hien tai

### 1. `filename` dang la object key truc tiep

Neu hai user cung upload `video.mp4`, object co the bi trung key. Nen tao key rieng:

```text
videos/{user_id}/{uuid}_{safe_filename}
```

### 2. `file_type` dang tach extension nhung khong dung

Trong `/complete`, bien `file_type = os.path.splitext(filename)[1]...` duoc tao nhung record van luu `FileType.VIDEO.value`. Neu chi cho upload video thi khong sao, nhung neu mo rong cho audio/image thi can tach ro logic.

### 3. Chua abort multipart upload khi client bo do

Neu client init nhung khong complete, cac part tam co the ton tai tren MinIO. Nen co job don rac goi `abort_multipart_upload` cho session qua han.

### 4. Nen validate user truoc khi complete

Endpoint `/complete` nhan `user_id` va tao record. Nen kiem tra user ton tai nhu endpoint upload video thuong dang lam.

## Trang thai media sau khi complete

Sau khi MinIO ghep object thanh cong, project tao `Media`:

```python
status=Status.PENDING.value
```

Y nghia: file goc da upload xong, nhung thumbnail/transcode/metadata chua xu ly. Cronjob hoac worker FFmpeg se doc cac record `PENDING`, doi sang `CONVERTING`, xu ly xong thi doi sang `COMPLETE` hoac `FAIL`.

## Checklist production

- Tao object key khong trung.
- Gioi han content type va extension.
- Gioi han file size theo user/quota.
- Luu `upload_id`, `object_key`, `expires_at` neu can resume upload.
- Sap xep parts theo `PartNumber` truoc khi complete.
- Abort multipart upload bi bo do.
- Sau complete, probe file de lay duration/resolution neu can.
