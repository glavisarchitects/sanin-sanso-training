<<<<<<< HEAD
<<<<<<< HEAD
# sanin-sanso-training
=======
# sanin-sanso-it
>>>>>>> 3d07c15a22afefbbfc2f844399a06278a804a87b
=======
# sanin-sanso

[FIX] [ADD] [UPDATE]

## 2021/08/16: init app

## Coding Convention 
	-Các model,view được dev trong dự án này sẽ được lưu dưới thư mục sanin-sanso 
	(checkout thư mục trên SVN)
	-Thêm comment bằng tiếng Anh hoặc copy tiếng Nhật từ file thiết kế
	-Format code trước khi save file

## Naming Convention
	1. Tạo module mới
		x.NewModuleName.NewModelName
		Ví dụ: tạo mới module master approval và model request
		=> x.masterapprovals.request
	
	2. Kế thừa module đã có, tạo model mới
		x.CurrentModuleName.ModelName
		Ví dụ: kế thừa module purchase, tạo mới model vendor approval
		=> x.purchase.vendorrequest
	
	3. Kế thừa module đã có, thêm trường vào model đã có
		x.CurrentModuleName.CurrentModelName
		Ví du: thêm trường vào model purchase.order
		=> purchase.order
	
	4. Thêm trường mới
		x_fieldName
<<<<<<< HEAD
>>>>>>> 34734a1cd343ab0f4831adc02bd0cb9673eade71
=======
>>>>>>> c71b866529dbfedca80807927506044965315b62
>>>>>>> 3d07c15a22afefbbfc2f844399a06278a804a87b
