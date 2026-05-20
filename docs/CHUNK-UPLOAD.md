# Chunk Upload

## Muc tieu

Chunk upload la cach chia mot file lon thanh nhieu phan nho de upload lan luot hoac song song. Cach nay giup he thong upload video lon on dinh hon vi moi request chi mang mot luong du lieu vua phai, co the retry tung phan loi ma khong phai gui lai ca file.

Trong project nay co hai cach minh hoa:

- `CronJobDo/serverTest.py`: backend nhan tung chunk, luu vao thu muc tam, sau do merge lai tren o dia.
- `Server/api/upload_video/routes.py`: backend tao multipart upload tren MinIO/S3, client upload truc tiep tung part bang presigned URL, backend chi goi complete de S3 ghep file.

## Luong xu ly co ban

```text
Client chon file
  -> tinh file_size va so chunk
  -> gui tung chunk len backend hoac S3
  -> nhan ETag/ket qua cua tung chunk
  -> bao complete
  -> backend/S3 ghep file
  -> tao media record status = PENDING
```

## Tai sao can chunk

Upload truc tiep mot file lon bang mot request de gap cac van de:

- Request qua lau, de bi timeout.
- Mang yeu lam hong ca file.
- Backend phai giu ket noi lon trong thoi gian dai.
- Neu upload that bai o 99%, client phai gui lai tu dau.

Khi chia chunk, moi chunk la mot don vi retry rieng. Neu part so 7 loi thi chi can gui lai part so 7.

## Cac truong du lieu quan trong

Mot protocol chunk upload nen co cac thong tin sau:

| Truong | Y nghia |
| --- | --- |
| `filename` | Ten file logic tren storage |
| `file_size` | Tong kich thuoc file, dung de tinh so chunk |
| `chunk_size` | Kich thuoc moi chunk, vi du 5 MB |
| `chunk_index` hoac `part_number` | Thu tu chunk |
| `total_chunks` | Tong so chunk can co |
| `upload_id` | Dinh danh mot phien multipart upload |
| `etag` | Bien lai cua S3/MinIO sau khi upload thanh cong mot part |

## Thu tu chunk

Khi backend tu merge chunk tren o dia, thu tu la bat buoc. Neu ghi chunk theo sai thu tu, file ket qua se hong.

Vi du trong `CronJobDo/serverTest.py`, backend merge bang vong lap:

```python
for i in range(total_chunks):
    chunk_path = os.path.join(file_chunks_folder, str(i))
    with open(chunk_path, "rb") as chunk_file:
        final_file.write(chunk_file.read())
```

Vi vay client phai dat ten chunk theo index lien tuc tu `0` den `total_chunks - 1`.

## Kich thuoc chunk

Chunk nho:

- De retry nhanh hon.
- Nhieu request hon.
- Tang overhead network va storage metadata.

Chunk lon:

- It request hon.
- Retry ton thoi gian hon khi loi.
- De cham toi timeout neu mang yeu.

Voi S3 multipart, part size nen tu 5 MB tro len, tru part cuoi cung co the nho hon. Project dang dung `CHUNK_SIZE` mac dinh `5 * 1024 * 1024` trong `Server/core/settings.py`, phu hop voi multipart upload.

## Loi thuong gap

| Loi | Nguyen nhan | Cach xu ly |
| --- | --- | --- |
| Thieu chunk | Client upload thieu hoac request loi | Check du part truoc khi merge/complete |
| Sai thu tu | Sort theo chuoi thay vi so, vi du `10` dung truoc `2` | Sort bang numeric index |
| File merge hong | Chunk bi ghi trung, sai offset, sai thu tu | Luu checksum hoac so sanh size |
| Timeout | Chunk qua lon hoac server xu ly cham | Giam chunk size, retry co backoff |
| Trung filename | Nhieu user upload cung ten file | Them UUID hoac prefix theo user/upload id |

## Checklist khi implement

- Tao upload session truoc khi upload chunk.
- Validate `file_size`, `chunk_size`, `total_chunks`.
- Khong tin filename goc tu client; can sanitize hoac tao object key moi.
- Cho phep retry idempotent: gui lai chunk cung index khong lam hong session.
- Sau khi complete thanh cong moi tao/cap nhat media record sang `PENDING`.
- Co co che abort/don rac voi upload session bi bo do.
