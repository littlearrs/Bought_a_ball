import ffmpeg


input_file = "E:\object_detection_dataset\well_data\well_demo2.avi"
output_file = "E:\object_detection_dataset\well_data\well_demo2.mp4"

ffmpeg.input(input_file).output(output_file, vcodec="libx264", acodec="aac").run()
