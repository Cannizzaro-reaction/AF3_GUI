from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
from convert import convert_pdb
import pandas as pd
from get_interaction import Interaction
import shutil

app = Flask(__name__)
app.secret_key = "dev_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads/"

# 确保上传文件夹存在
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    return render_template("upload.html")


@app.route("/find-residue-pairs")
def find_residue_pairs():
    return render_template("find_residue_pairs.html")


@app.route("/count-interactions")
def count_interactions():
    return render_template("count_interactions.html")


@app.route("/visualization")
def visualization():
    return render_template("visualization.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/upload", methods=["POST"])
def upload_files():
    if "file1" not in request.files or "file2" not in request.files:
        return jsonify({"success": False}), 400

    file1 = request.files["file1"]
    file2 = request.files["file2"]

    if file1.filename == "" or file2.filename == "":
        return jsonify({"success": False}), 400

    upload_folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    if not file1.filename.endswith(".json"):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "The first file you uploaded is not a JSON file",
                }
            ),
            400,
        )

    if not file2.filename.endswith(".cif"):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "The second file you uploaded is not a CIF file",
                }
            ),
            400,
        )

    # 保存文件并存储文件路径到 session
    filepath1 = os.path.join(app.config["UPLOAD_FOLDER"], file1.filename)
    file1.save(filepath1)
    session["filepath1"] = filepath1
    print(f".json path: {filepath1}")

    filepath2 = os.path.join(app.config["UPLOAD_FOLDER"], file2.filename)
    file2.save(filepath2)
    print(f".cif path: {filepath2}")

    pdb_filename2 = file2.filename.rsplit(".", 1)[0] + ".pdb"
    pdb_filepath2 = os.path.join(app.config["UPLOAD_FOLDER"], pdb_filename2)

    try:
        convert_pdb(filepath2, pdb_filepath2)
        if os.path.exists(pdb_filepath2):
            session["pdb_filepath2"] = pdb_filepath2
            print("PDB file path saved to session:", pdb_filepath2)
        else:
            print("Failed to convert or save PDB file")
            return (
                jsonify({"success": False, "message": "PDB file conversion failed"}),
                500,
            )
    except Exception as e:
        print(f"Error converting CIF to PDB: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

    return jsonify(
        {"success": True, "filepath1": filepath1, "pdb_filepath2": pdb_filepath2}
    )


@app.route("/clear-uploads", methods=["POST"])
def clear_uploads():
    folder = os.path.join(app.config["UPLOAD_FOLDER"])
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Failed to delete {filename}. {str(e)}",
                    }
                ),
                500,
            )
    return jsonify({"success": True})


@app.route("/clear_files", methods=["POST"])
def clear_files():
    folder = "analysis_result"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            return (
                jsonify({"error": "Failed to delete " + filename, "message": str(e)}),
                500,
            )

    return jsonify({"message": "All result files were deleted successfully"})


@app.route("/generate_csv", methods=["POST"])
def generate_csv():
    try:
        # 从 session 中获取路径
        filepath1 = session.get("filepath1")
        pdb_filepath2 = session.get("pdb_filepath2")

        if not filepath1 or not pdb_filepath2:
            return jsonify({"error": "File paths not set"}), 400

        n = int(request.args.get("n", 10))

        # 使用 Interaction 类生成 CSV
        interaction = Interaction(json_path=filepath1, pdb_path=pdb_filepath2)
        interaction.write_interactions_to_csv()

        # 读取并返回 CSV 文件内容
        csv_file_path = "analysis_result/PAE_b-factor.csv"
        if not os.path.exists(csv_file_path):
            return jsonify({"error": "CSV file was not created"}), 500

        # 读取 CSV 并排序
        df = pd.read_csv(csv_file_path)
        df_sorted = df.sort_values(by="Contact_Prob", ascending=False)

        # 选择前 n 个，并包括所有具有相同 Contact_Prob 的额外行
        if n < len(df_sorted):
            last_prob = df_sorted.iloc[n - 1]["Contact_Prob"]
            top_n = df_sorted[df_sorted["Contact_Prob"] >= last_prob]
        else:
            top_n = df_sorted

        result = top_n.to_dict(orient="records")

        # Save CSV with dynamic naming
        csv_filename = f"top{n}_interaction.csv"
        csv_path = os.path.join("analysis_result", csv_filename)
        top_n.to_csv(csv_path, index=False)

        # print(result)
        return jsonify(
            {
                "data": result,
                "csvPath": csv_filename,
                "fullPath": "PAE_b-factor.csv",
                "message": "Data processed",
            }
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route("/get_top_n")
def get_top_n():
    n = int(request.args.get("n"))
    filepath1 = session.get("filepath1")
    pdb_filepath2 = session.get("pdb_filepath2")

    if not filepath1 or not pdb_filepath2:
        return jsonify({"error": "File paths not set"}), 400
    interaction = Interaction(json_path=filepath1, pdb_path=pdb_filepath2)

    csv_file_path = os.path.join(interaction.result_dir, "PAE_b-factor.csv")
    df = pd.read_csv(csv_file_path)
    df_sorted = df.sort_values(by="Contact_Prob", ascending=False)
    top_n = df_sorted.head(n)
    result = top_n.to_dict(orient="records")

    return jsonify(result)


def format_decimals(df, n=2):
    for column in df.columns:
        if df[column].dtype == "float64":
            df[column] = df[column].round(n)  # 将所有浮点数列四舍五入到两位小数
    return df


@app.route("/count-interactions", methods=["GET", "POST"])
def get_count():
    # get parameters
    n = int(request.form.get("rangeSlider", 10))

    user_choice_chain = request.form.get("chain")
    chain_mapping = {"chainA": "A", "chainB": "B"}
    chain = chain_mapping.get(user_choice_chain)

    user_choice_method = request.form.get("method")
    method_mapping = {
        "interaction_number": "Interaction_Count",
        "total_contact_probability": "Total_Contact_Prob",
    }
    method = method_mapping.get(user_choice_method)

    filepath1 = session.get("filepath1")
    pdb_filepath2 = session.get("pdb_filepath2")
    if not filepath1 or not pdb_filepath2:
        return jsonify({"error": "File paths not set"}), 400

    interaction = Interaction(json_path=filepath1, pdb_path=pdb_filepath2)
    # get file: PAE_b-factor.csv
    interaction.write_interactions_to_csv()
    df, csv_path = interaction.n_interaction_count(chain, n, method)
    df = format_decimals(df)
    # print(df)
    result = df.to_dict(orient="records")

    # Save CSV with dynamic naming
    csv_filename = f"top{n}_chain{chain}_by_{method}.csv"
    csv_path = os.path.join("analysis_result", csv_filename)
    df.to_csv(csv_path, index=False)

    # print(result)
    return jsonify(
        {"data": result, "csvPath": csv_filename, "message": "Data processed"}
    )


@app.route("/generate_images", methods=["POST"])
def generate_images():
    filepath1 = session.get("filepath1")
    pdb_filepath2 = session.get("pdb_filepath2")
    # print(f"File path 1: {filepath1}")
    # print(f"PDB file path 2: {pdb_filepath2}")

    user_choice_chain = request.form.get("chain")
    # print("Received chain:", user_choice_chain)

    if not user_choice_chain:
        # print("Error: Chain parameter is missing")
        return jsonify({"error": "Chain parameter is missing"}), 400

    chain_mapping = {"chainA": "A", "chainB": "B"}
    chain_id = chain_mapping.get(user_choice_chain)
    # print(f"chain_id received: {chain_id}")

    if not chain_id:
        return jsonify({"error": "Invalid chain selected"}), 400

    """
    if not filepath1 or not pdb_filepath2:
        print("File paths error.")
        return jsonify({"error": "File paths not set"}), 400
    """

    interaction = Interaction(json_path=filepath1, pdb_path=pdb_filepath2)
    # get file: PAE_b-factor.csv
    interaction.write_interactions_to_csv()
    # print("Data collected.")
    try:
        interaction.interaction_map()
        interaction.plot_interaction_summary(chain_id)
        return jsonify({"message": "Images generated successfully"})
    except Exception as e:
        print(f"Error generating images: {e}")  # 记录错误信息
        return jsonify({"error": "Failed to generate images"}), 500


@app.route("/images/<filename>")
def get_image(filename):
    return send_from_directory("analysis_result", filename)


@app.route("/search-residue", methods=["POST"])
def search_residue():
    filepath1 = session.get("filepath1")
    pdb_filepath2 = session.get("pdb_filepath2")
    if not filepath1 or not pdb_filepath2:
        return jsonify({"error": "File paths not set"}), 400

    user_choice_chain = request.form.get("chain")
    residue_num_str = request.form.get("numberInput")

    if not residue_num_str:
        return jsonify({"error": "Residue number not provided"}), 400

    try:
        residue_num = int(residue_num_str)
    except ValueError:
        return jsonify({"error": "Invalid residue number"}), 400

    chain_mapping = {"chainA": "A", "chainB": "B"}
    chain = chain_mapping.get(user_choice_chain)

    if not chain:
        return jsonify({"error": "Invalid chain selected"}), 400

    interaction = Interaction(json_path=filepath1, pdb_path=pdb_filepath2)
    interaction.write_interactions_to_csv()

    if chain == "A":
        residue_max = interaction.len_A
    else:
        residue_max = interaction.len_B

    if residue_num > residue_max:
        return (
            jsonify({"error": "The input number exceeds the length of the chain"}),
            400,
        )

    csv_path, df = interaction.query_interactions(chain, residue_num)
    df = format_decimals(df)
    result = df.to_dict(orient="records")

    # Save CSV with dynamic naming
    csv_filename = f"interaction_{chain}_{residue_num}.csv"
    csv_path = os.path.join("analysis_result", csv_filename)
    df.to_csv(csv_path, index=False)

    return jsonify(
        {"data": result, "csvPath": csv_filename, "message": "Data processed"}
    )


@app.route("/download-csv/<filename>")
def download_csv(filename):
    directory = os.path.join(app.root_path, "analysis_result")  # 文件存放目录
    return send_from_directory(directory, filename, as_attachment=True)


@app.route("/download-image/<filename>")
def download_image(filename):
    directory = os.path.join(app.root_path, "analysis_result")
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
