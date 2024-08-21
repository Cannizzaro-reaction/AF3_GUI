import json
import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as patches
import matplotlib.colors as mcolors
from collections import defaultdict
from matplotlib.colors import LinearSegmentedColormap
from Bio.PDB import PDBParser
import os
import json
from datetime import datetime


class Interaction:
    def __init__(self, json_path, pdb_path):
        # load data from .json file
        self.json_path = json_path
        self.data = self._load_json(json_path)

        # load data from .pdb file
        self.pdb_path = pdb_path

        # get data from the dictionary in .json file accordingly
        self.contact_probs = self.data["contact_probs"]
        self.pae = self.data["pae"]
        self.token_chain_ids = self.data["token_chain_ids"]
        self.token_res_ids = self.data["token_res_ids"]

        # count the number of residues in chain A and chain B
        self.len_A = self.token_chain_ids.count("A")
        self.len_B = self.token_chain_ids.count("B")
        self.len_total = self.len_A + self.len_B

    def _load_json(self, json_path):
        """Load data in .json path and return."""
        with open(json_path, "r") as f:
            return json.load(f)

    def _calculate_accuracy(self):
        """
        Calculate the average b-factor of a residue from all of the atoms.
        The bigger this value, the less stable of the atom.
        The return values are the average b-factor of a certain residue and its residue-order number.
        """
        parser = PDBParser()
        structure = parser.get_structure("structure_name", self.pdb_path)

        b_factors = defaultdict(list)
        """
        Record the b-factor of each residue.
        key: chain_id-residue_id
        value: mean b-factor
        """
        residue_names = {}  # record the names of the residues
        residue_order = []  # get the order of the residues

        for model in structure:
            for chain in model:
                chain_id = chain.id  # A or B
                for residue in chain:
                    res_id = residue.get_id()[1]  # get the No. of residue
                    residue_key = f"{chain_id}{res_id}"
                    residue_order.append(residue_key)
                    residue_names[residue_key] = (
                        residue.get_resname()
                    )  # get the names of the residues
                    for atom in residue:
                        b_factors[residue_key].append(atom.get_bfactor())

        # calculate the mean b-factor and return the avg_b_factors dictionary
        avg_b_factors = {
            key: [residue_names[key], np.mean(values)]
            for key, values in b_factors.items()
        }
        """
        avg_b_factors: a dictionary
        key: {chain_id}{residue No.}
        value: a list, value[0] = residue name, value[1] = mean b-factor
        """
        return avg_b_factors, residue_order

    def _calculate_pae_accuracy(self, residue_order):
        """
        Calculate the mean PAE value of a given residue.
        e.g. 'A1': ['MET', 19.63375], 'B90': ['LYS', 68.69444444444444]
        The PAE value means the accuracy of the residue's relative position towards other atoms.
        """
        return {
            residue_key: np.mean(self.pae[i])
            for i, residue_key in enumerate(residue_order)
            if i < len(self.pae)
        }

    def get_combined_results(self):
        # combine the results as: (id, residue, average B factor, average PAE value)
        avg_b_factors, residue_order = (
            self._calculate_accuracy()
        )  # residue_order: like 'B89'
        avg_pae_values = self._calculate_pae_accuracy(residue_order)
        combined_results = {
            key: {
                "Residue": avg_b_factors[key][0],
                "Average B-factor": avg_b_factors[key][1],
                "Average PAE value": avg_pae_values.get(key, None),
            }
            for key in avg_b_factors.keys()
        }
        return combined_results

    def print_combined_results(self):
        """
        Print combined results like:
        B188: Residue PRO, Average B-factor: 76.96, Average PAE value: 24.92
        """
        combined_results = self.get_combined_results()
        for key, values in combined_results.items():
            print(
                f"{key}: Residue {values['Residue']}, Average B-factor: {values['Average B-factor']:.2f}, Average PAE value: {values['Average PAE value']:.2f}"
            )

    def _write_to_csv(self, rows, fieldnames):
        os.makedirs("analysis_result", exist_ok=True)
        result_file = "analysis_result/PAE_b-factor.csv"
        with open(result_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                formatted_row = {
                    key: f"{value:.3f}" if isinstance(value, float) else value
                    for key, value in row.items()
                }
                writer.writerow(formatted_row)

    def write_interactions_to_csv(self):
        """
        Find out interaction pairs and write the combined results to a .csv file.
        The output file includes the average PAE and b-factor of the two residues respectively,
        the PAE score between these two residues,
        and the contact probabiliy.
        """
        combined_results = self.get_combined_results()
        fieldnames = [
            "Chain_1",
            "Residue_1",
            "Residue_1_Name",
            "Average_B_factor_1",
            "Average_PAE_1",
            "Chain_2",
            "Residue_2",
            "Residue_2_Name",
            "Average_B_factor_2",
            "Average_PAE_2",
            "PAE",
            "Contact_Prob",
        ]

        rows = [
            {
                "Chain_1": self.token_chain_ids[i],
                "Residue_1": self.token_res_ids[i],
                "Residue_1_Name": combined_results.get(
                    f"{self.token_chain_ids[i]}{self.token_res_ids[i]}", {}
                ).get("Residue", "N/A"),
                "Average_B_factor_1": combined_results.get(
                    f"{self.token_chain_ids[i]}{self.token_res_ids[i]}", {}
                ).get("Average B-factor", np.nan),
                "Average_PAE_1": combined_results.get(
                    f"{self.token_chain_ids[i]}{self.token_res_ids[i]}", {}
                ).get("Average PAE value", np.nan),
                "Chain_2": self.token_chain_ids[j],
                "Residue_2": self.token_res_ids[j],
                "Residue_2_Name": combined_results.get(
                    f"{self.token_chain_ids[j]}{self.token_res_ids[j]}", {}
                ).get("Residue", "N/A"),
                "Average_B_factor_2": combined_results.get(
                    f"{self.token_chain_ids[j]}{self.token_res_ids[j]}", {}
                ).get("Average B-factor", np.nan),
                "Average_PAE_2": combined_results.get(
                    f"{self.token_chain_ids[j]}{self.token_res_ids[j]}", {}
                ).get("Average PAE value", np.nan),
                "PAE": self.pae[self.token_res_ids.index(self.token_res_ids[i])][
                    self.token_res_ids.index(self.token_res_ids[j])
                ],
                "Contact_Prob": prob,
            }
            for i, row in enumerate(self.contact_probs)
            for j, prob in enumerate(row)
            if prob > 0
            and self.token_chain_ids[i] == "A"
            and self.token_chain_ids[j] == "B"
        ]
        self._write_to_csv(rows, fieldnames)

    def interaction_count(self, chain):
        """
        Analyze interactions for a specified chain ('A' or 'B') and write results to a new CSV file,
        including Average B-factor and Average PAE for each residue. Each residue will only have one set of B-factor and PAE.
        """
        # Decide which residue and B-factor/PAE columns to use based on the chain
        if chain == "A":
            residue_column = "Residue_1"
            residue_name_column = "Residue_1_Name"
            chain_column = "Chain_1"
            b_factor_column = "Average_B_factor_1"
            pae_column = "Average_PAE_1"
        elif chain == "B":
            residue_column = "Residue_2"
            residue_name_column = "Residue_2_Name"
            chain_column = "Chain_2"
            b_factor_column = "Average_B_factor_2"
            pae_column = "Average_PAE_2"
        else:
            raise ValueError("Chain must be 'A' or 'B'.")

        interactions = {}
        interaction_df = pd.read_csv("analysis_result/PAE_b-factor.csv")

        # Process rows based on specified chain
        for index, row in interaction_df.iterrows():
            if row[chain_column] == chain:
                residue_key = f"{row[residue_column]}-{row[residue_name_column]}"
                if residue_key not in interactions:
                    interactions[residue_key] = {
                        "interaction_count": 0,
                        "total_contact_prob": 0,
                        "average_b_factor": row[b_factor_column],
                        "average_pae": row[pae_column],
                    }
                interactions[residue_key]["interaction_count"] += 1
                interactions[residue_key]["total_contact_prob"] += row["Contact_Prob"]

        # Prepare data to write to CSV
        fieldnames = [
            "Residue_ID",
            "Residue_Name",
            "Interaction_Count",
            "Total_Contact_Prob",
            "Average_B_Factor",
            "Average_PAE",
        ]
        rows = [
            {
                "Residue_ID": key.split("-")[0],
                "Residue_Name": key.split("-")[1],
                "Interaction_Count": details["interaction_count"],
                "Total_Contact_Prob": details["total_contact_prob"],
                "Average_B_Factor": details["average_b_factor"],
                "Average_PAE": details["average_pae"],
            }
            for key, details in interactions.items()
        ]

        # Define the CSV output file name
        csv_file_name = f"analysis_result/interactions_{chain}.csv"
        with open(csv_file_name, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # print(f"Data written to {csv_file_name}")

    def n_interaction_count(self, chain, n, method):
        """
        chain: 'A' or 'B'
        n: a number get by slider
        method: 'Interaction_Count' or 'Total_Contact_Prob'
        """
        self.interaction_count(chain)  # Assume this function properly sets up the data
        file_path = f"./analysis_result/interactions_{chain}.csv"
        df_interaction_count = pd.read_csv(file_path)
        df_count_sorted = df_interaction_count.sort_values(by=method, ascending=False)

        # Ensure the index value n-1 exists in the DataFrame
        if n <= len(df_count_sorted):
            nth_value = df_count_sorted.iloc[n - 1][method]  # Get the nth value
            top_n = df_count_sorted[
                df_count_sorted[method] >= nth_value
            ]  # Select all rows that have the same or greater value
        else:
            top_n = (
                df_count_sorted  # If n is out of bounds, return the entire sorted list
            )

        # save to csv
        csv_path = f"analysis_result/top{n}_chain{chain}_by_{method}.csv"
        top_n.to_csv(csv_path, index=False)

        # print(top_n)
        return top_n, csv_path

    def interaction_map(self):
        """
        Plot the interaction between the two chains.
        Each dot represents an interaction.
        The color of the dot represents the contact probability.
        """
        # get data from PAE_b-factor.csv
        data_path = "analysis_result/PAE_b-factor.csv"
        interaction_df = pd.read_csv(data_path)

        # set the longer chain as xlim
        if interaction_df["Residue_1"].max() > interaction_df["Residue_2"].max():
            x_data, y_data = "Residue_1", "Residue_2"
        else:
            x_data, y_data = "Residue_2", "Residue_1"

        # set color gradient for contact probability
        norm = plt.Normalize(
            vmin=interaction_df["Contact_Prob"].min(),
            vmax=interaction_df["Contact_Prob"].max(),
        )
        colors = [
            "#7b9971",
            "#85a170",
            "#90a96f",
            "#9db06e",
            "#abb76c",
            "#b4be68",
            "#bec564",
            "#c8cb5f",
            "#cdd356",
            "#d3db4c",
            "#d7e43f",
            "#dcec30",
        ]
        cmap = mcolors.LinearSegmentedColormap.from_list("CustomCmap", colors)

        plt.figure(figsize=(12, 8))
        ax = plt.gca()

        # set a transparent background
        ax.patch.set_alpha(0)
        ax.patch.set_visible(False)

        # plot a bubble map with fixed bubble size
        scatter = plt.scatter(
            interaction_df[x_data],
            interaction_df[y_data],
            s=15,  # fixed size for all dots
            c=interaction_df["Contact_Prob"],
            cmap=cmap,
            norm=norm,
            alpha=0.5,
            edgecolor="none",
        )

        plt.colorbar(scatter, label="Contact Probability")
        plt.title("Residue Interaction Map")
        plt.xlabel(f"{x_data}")
        plt.ylabel(f"{y_data}")
        plt.tight_layout()

        # plt.show()

        output_path = "analysis_result/bubble_map.png"
        plt.savefig(output_path, format="png", dpi=300, transparent=True)
        plt.close()

        print("1st images saved successfully")

    def plot_interaction_summary(self, chain_id):
        print(f"Generating images for chain {chain_id}")

        # get data from PAE_b-factor.csv
        data_path = "analysis_result/PAE_b-factor.csv"
        interaction_df = pd.read_csv(data_path)

        # calculate the total contact number and the sum of contact probability of each residue in the chain selected
        chain_residues = [
            res
            for res, chain in zip(self.token_res_ids, self.token_chain_ids)
            if chain == chain_id
        ]
        interaction_count = defaultdict(int)
        interaction_sum = defaultdict(float)

        if chain_id == "A":
            for _, row in interaction_df.iterrows():
                if row["Residue_1"] in chain_residues:
                    interaction_count[row["Residue_1"]] += 1
                    interaction_sum[row["Residue_1"]] += row["Contact_Prob"]
                    residues = list(range(self.len_A + 1))

        if chain_id == "B":
            for _, row in interaction_df.iterrows():
                if row["Residue_2"] in chain_residues:
                    interaction_count[row["Residue_2"]] += 1
                    interaction_sum[row["Residue_2"]] += row["Contact_Prob"]
                    residues = list(range(self.len_B + 1))

        # make sure that the residues without interaction can also be recorded with a value 0
        counts = [interaction_count.get(res, 0) for res in residues]
        sums = [interaction_sum.get(res, 0.0) for res in residues]

        # plot the line chart
        fig, ax1 = plt.subplots(figsize=(12, 4))

        color_count = "#405C38"
        color_sum = "#A29045"
        ax1.plot(
            residues,
            counts,
            "-",
            label="Interaction Count",
            linewidth=1,
            color=color_count,
        )
        ax1.set_xlabel(f"Chain {chain_id} Residue")
        ax1.set_ylabel("Interaction Count", color=color_count)
        ax1.tick_params(axis="y", labelcolor=color_count)

        ax2 = ax1.twinx()
        ax2.plot(
            residues, sums, "-", label="Interaction Sum", linewidth=1, color=color_sum
        )
        ax2.set_ylabel("Interaction Sum", color=color_sum)
        ax2.tick_params(axis="y", labelcolor=color_sum)

        # fill the color between x-axis and the line
        ax1.fill_between(residues, 0, counts, color="#7B9971", alpha=0.3)
        ax2.fill_between(residues, 0, sums, color="#DBC678", alpha=0.3)

        # revere the x-axis (form the biggest to the smallest)
        # ax1.set_xlim(max(residues), min(residues))
        # ax2.set_xlim(max(residues), min(residues))

        # set the legend
        lines = [
            plt.Line2D([0], [0], color=color_count, lw=3),
            plt.Line2D([0], [0], color=color_sum, lw=3),
        ]
        ax1.legend(lines, ["Interaction Count", "Interaction Sum"], loc="upper left")

        plt.title("Interaction Count and Sum")
        plt.tight_layout()

        # set transparent background color
        fig.patch.set_facecolor("none")
        ax1.set_facecolor("none")
        ax2.set_facecolor("none")

        # save as .png file
        output_path = "analysis_result/interaction_summary.png"
        plt.savefig(output_path, format="png", dpi=300, transparent=True)
        # plt.show()
        print("2nd images saved successfully")

    def query_interactions(self, chain_id, res_id=int):
        if chain_id == "A":
            chain_A_index = self.token_res_ids.index(res_id)
            interactions = self.contact_probs[chain_A_index][self.len_A :]
            interacting_residues = [
                f"B{self.token_res_ids[self.len_A + i]}"
                for i in range(self.len_B)
                if interactions[i] > 0
            ]
        elif chain_id == "B":
            chain_B_index = self.token_res_ids.index(res_id)
            interactions = self.contact_probs[self.len_A + chain_B_index][: self.len_A]
            interacting_residues = [
                f"A{self.token_res_ids[i]}"
                for i in range(self.len_A)
                if interactions[i] > 0
            ]
        else:
            print("Invalid chain id. Please use 'A' or 'B'.")
            return

        combined_results = self.get_combined_results()

        results = []
        residue_key = f"{chain_id}{res_id}"
        query_res_name = combined_results[residue_key]["Residue"]
        residue_info = f"{chain_id}{res_id}_{query_res_name}"
        for inter_residue in interacting_residues:
            if inter_residue in combined_results:
                results.append(
                    {
                        "residue_number": inter_residue,
                        "residue_name": combined_results[inter_residue]["Residue"],
                        "b_factor": combined_results[inter_residue]["Average B-factor"],
                        "PAE": combined_results[inter_residue]["Average PAE value"],
                        "contact_probability": str(
                            interactions[
                                self.token_res_ids.index(int(inter_residue[1:]))
                            ]
                        ),
                    }
                )

        # write results to csv
        df = pd.DataFrame(results)
        csv_path = f"analysis_result/{residue_info}.csv"
        df.to_csv(csv_path, index=False)
        # print(df)

        return csv_path, df


################### test ###################
# interaction = Interaction(
#     r"./uploads/fold_2024_07_15_16_51_full_data_0.json",
#     r"./uploads/fold_2024_07_15_16_51_model_0.pdb",
# )
# interaction.plot_interaction_summary("B")
# interaction.interaction_map()
# interaction.query_interactions("A", 296)
