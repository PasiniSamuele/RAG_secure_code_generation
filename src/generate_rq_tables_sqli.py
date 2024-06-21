import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
def from_dataset_to_splits(row):
   dataset = row["dataset"]
   #check in dataset ends with zero_shot or rag
   if dataset.endswith("zero_shot") or dataset.endswith("rag"):
      dataset = dataset +"_0"
   #print(dataset)
   parts = dataset.split("_")
   generation = "_".join(parts[2:-1])
   row["dataset_model"] = parts[0]
   row["dataset_temperature"] = parts[1]
   row["dataset_generation_mode"] = 0 if generation == "zero_shot" or generation == "few_shot" else 1
   row["dataset_examples_per_class"] = parts[3]
   return row

def create_experiment(row):
    row['experiment'] = row['model_name']+'_'+str(row['temperature'])+'_'+row['generation_mode']+'_'+str(row['examples_per_class'])
    return row

#test_results_file_old_sap = "old_experiments_sap/task_detect_xss_simple_prompt/experiments_summary_test.csv"
#test_results_file_sap = "new_experiments_sap/task_detect_xss_simple_prompt/experiments_summary_test.csv"
test_results_file = "experiments/task_detect_sqli_extended/template_create_function_readable/experiments_summary_test.csv"
#test_synth_results_file = "experiments/task_detect_xss_simple_prompt/test_results_synth.csv"

gen_rq1 = True
gen_rq2 = False

rq1_file = "rq1_sqli.csv"

rq2_file = "rq2.csv"

rq1_plot_folder = "rq1_plots_sqli"
rq2_plot_folder = "rq2_plots"

exps_scenario = {
    "best": {
        "experiment":"gpt-4-0125-preview_0.0_rag_few_shot_5",
        "datasets":{
            "best": "gpt-4-0125-preview_0.0_few_shot_5",
            "avg":"gpt-4-0125-preview_0.5_few_shot_3",
            "worst":"gpt-4-0125-preview_0.5_few_shot_3"
        }},

}

best_exp = "gpt-4-0125-preview_0.0_rag_few_shot_5"
worst_case = "gpt-4-0125-preview_1.0_zero_shot_0"
middle_case = "gpt-4-0125-preview_0.5_few_shot_3"

dataset_to_keep = "gpt-4-0125-preview_1.0_rag_few_shot_5"

if gen_rq1:
    #df = pd.concat([pd.read_csv(test_results_file),pd.read_csv(test_results_file_sap), pd.read_csv(test_results_file_old_sap)])
    df = pd.read_csv(test_results_file)
    examples_values = set(df["examples_per_class"].values.tolist())
    new_columns = ["model_temperature"]
    new_columns.extend(list(map(lambda x:f"no_rag_{x}",examples_values)))
    new_columns.extend(list(map(lambda x:f"rag_{x}",examples_values)))
    new_df = pd.DataFrame(columns=new_columns)
    df["model_temperature"] = df["model_name"]+"_"+df["temperature"].astype(str)
    df = df.sort_values(by=["model_temperature"])
    success_improvement_df = pd.DataFrame(columns=["model_temperature","examples_per_class","success_improvement"])
    rag_improvement_df = pd.DataFrame(columns=["model_temperature","examples_per_class","rag_improvement"])
    var_improvement_df = pd.DataFrame(columns=["model_temperature","examples_per_class","var_improvement"])

    for model_temperature in df["model_temperature"].unique():
        #keep only the model_temperature with gpt-4 or claude-3
        if "gpt-4" not in model_temperature and "claude-3" not in model_temperature and "claude-v1" not in model_temperature and "3.5" not in model_temperature:
            continue
        df_model_temperature = df[df["model_temperature"]==model_temperature]
        new_row = {"model_temperature":model_temperature}
        for examples_per_class in examples_values:
            if int(examples_per_class) == 0:
                print(model_temperature, examples_per_class)
                # generation mode zero shot and examples per class = 0
                new_row[f"no_rag_{examples_per_class}"] = df_model_temperature[(df_model_temperature["generation_mode"]=="zero_shot") & (df_model_temperature["examples_per_class"]==0)]["accuracy"].values[0]
                # generation mode rag and examples per class = 0
                new_row[f"rag_{examples_per_class}"] = df_model_temperature[(df_model_temperature["generation_mode"]=="rag") & (df_model_temperature["examples_per_class"]==0)]["accuracy"].values[0]

                successes_without_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="zero_shot") & (df_model_temperature["examples_per_class"]==0)]["successes"].values[0]
                successes_with_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="rag") & (df_model_temperature["examples_per_class"]==0)]["successes"].values[0]
                if successes_without_rag <=20 or successes_with_rag <=20:
                    success_difference = successes_with_rag - successes_without_rag
                    success_improvement_df = pd.concat([success_improvement_df,pd.DataFrame({"model_temperature":model_temperature,"examples_per_class":examples_per_class,"success_improvement":success_difference},index=[0])])
                        
                if new_row[f"rag_{examples_per_class}"]!= 0 and new_row[f"no_rag_{examples_per_class}"]!= 0:
                    rag_difference =  new_row[f"rag_{examples_per_class}"] - new_row[f"no_rag_{examples_per_class}"]
                    rag_improvement_df = pd.concat([rag_improvement_df,pd.DataFrame({"model_temperature":model_temperature,"examples_per_class":examples_per_class,"rag_improvement":rag_difference},index=[0])])

                    accuracy_var_no_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="zero_shot") & (df_model_temperature["examples_per_class"]==0)]["accuracy_std"].values[0]
                    accuracy_var_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="rag") & (df_model_temperature["examples_per_class"]==0)]["accuracy_std"].values[0]
                    var_difference = accuracy_var_rag - accuracy_var_no_rag
                    var_improvement_df = pd.concat([var_improvement_df,pd.DataFrame({"model_temperature":model_temperature,"examples_per_class":examples_per_class,"var_improvement":var_difference},index=[0])])
            else:
                # generation mode few_shot and examples per class = examples per class
                new_row[f"no_rag_{examples_per_class}"] = df_model_temperature[(df_model_temperature["generation_mode"]=="few_shot") & (df_model_temperature["examples_per_class"]==examples_per_class)]["accuracy"].values[0]
                # generation mode rag_few_shot and examples per class = examples per class
                new_row[f"rag_{examples_per_class}"] = df_model_temperature[(df_model_temperature["generation_mode"]=="rag_few_shot") & (df_model_temperature["examples_per_class"]==examples_per_class)]["accuracy"].values[0]

                successes_without_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="few_shot") & (df_model_temperature["examples_per_class"]==examples_per_class)]["successes"].values[0]
                successes_with_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="rag_few_shot") & (df_model_temperature["examples_per_class"]==examples_per_class)]["successes"].values[0]
                if successes_without_rag <=20 or successes_with_rag <=20:
                    success_difference = successes_with_rag - successes_without_rag
                    success_improvement_df = pd.concat([success_improvement_df,pd.DataFrame({"model_temperature":model_temperature,"examples_per_class":examples_per_class,"success_improvement":success_difference},index=[0])])
                   
                if new_row[f"rag_{examples_per_class}"]!= 0 and new_row[f"no_rag_{examples_per_class}"]!= 0:
                    rag_difference =  new_row[f"rag_{examples_per_class}"] - new_row[f"no_rag_{examples_per_class}"]
                    rag_improvement_df = pd.concat([rag_improvement_df,pd.DataFrame({"model_temperature":model_temperature,"examples_per_class":examples_per_class,"rag_improvement":rag_difference},index=[0])])

                    accuracy_var_no_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="few_shot") & (df_model_temperature["examples_per_class"]==examples_per_class)]["accuracy_std"].values[0]
                    accuracy_var_rag = df_model_temperature[(df_model_temperature["generation_mode"]=="rag_few_shot") & (df_model_temperature["examples_per_class"]==examples_per_class)]["accuracy_std"].values[0]
                    var_difference = accuracy_var_rag - accuracy_var_no_rag
                    var_improvement_df = pd.concat([var_improvement_df,pd.DataFrame({"model_temperature":model_temperature,"examples_per_class":examples_per_class,"var_improvement":var_difference},index=[0])])
        new_df = pd.concat([new_df,pd.DataFrame(new_row,index=[0])], )

    new_df.to_csv(rq1_file,index=False,float_format='%.3f')
    sns.set_theme(style="whitegrid")

    os.makedirs(rq1_plot_folder, exist_ok=True)
    plt.figure(figsize=(10, 10))
    ax = sns.displot(data=rag_improvement_df, x=f"rag_improvement", palette = "hls", kind = "kde", linewidth = 2, fill = True)
    ax.figure.set_size_inches(10,8)
    [single_ax.set_title(f"Improvement of Avg Accuracy using RAG") for single_ax in ax.axes.flat]
    ax.set_xlabels("AVG Accuracy Difference")
    ax.set_ylabels("Density")
    [single_ax.set_xticks(np.arange(-0.5,0.5, 0.1)) for single_ax in ax.axes.flat]
    # [single_ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f')) for single_ax in ax.axes.flat]
    # [single_ax.set_xlim(-0.1,0.5) for single_ax in ax.axes.flat]
    # [single_ax.set_xticks(range(-0.1,0.5, 0.05)) for single_ax in ax.axes.flat]

    plt.savefig(os.path.join(rq1_plot_folder,f"rag_improvement.jpg"))
    plt.close()

    plt.figure(figsize=(10, 10))
    ax = sns.displot(data=success_improvement_df, x=f"success_improvement", palette = "hls", kind = "kde", linewidth = 2, fill = True, color = "red")
    ax.figure.set_size_inches(10,8)
    [single_ax.set_title(f"Improvement of Successes using RAG") for single_ax in ax.axes.flat]
    ax.set_xlabels("Successes Difference")
    ax.set_ylabels("Density")
    [single_ax.set_xticks(np.arange(-100 ,100, 10)) for single_ax in ax.axes.flat]
    # [single_ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f')) for single_ax in ax.axes.flat]
    # [single_ax.set_xlim(-0.1,0.5) for single_ax in ax.axes.flat]
    # [single_ax.set_xticks(range(-0.1,0.5, 0.05)) for single_ax in ax.axes.flat]

    plt.savefig(os.path.join(rq1_plot_folder,f"success_improvement.jpg"))
    plt.close()

    plt.figure(figsize=(10, 10))
    ax = sns.displot(data=var_improvement_df, x=f"var_improvement", palette = "hls", kind = "kde", linewidth = 2, fill = True, color = "green")
    ax.figure.set_size_inches(10,8)
    [single_ax.set_title(f"Improvement of Accuracy Variance using RAG") for single_ax in ax.axes.flat]
    ax.set_xlabels("Accuracy Variance Difference")
    ax.set_ylabels("Density")
    [single_ax.set_xticks(np.arange(-0.3,0.3, 0.05)) for single_ax in ax.axes.flat]
    # [single_ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f')) for single_ax in ax.axes.flat]
    # [single_ax.set_xlim(-0.1,0.5) for single_ax in ax.axes.flat]
    # [single_ax.set_xticks(range(-0.1,0.5, 0.05)) for single_ax in ax.axes.flat]

    plt.savefig(os.path.join(rq1_plot_folder,f"variance_improvement.jpg"))
    plt.close()

if gen_rq2:
    df = df.apply(create_experiment, axis=1)

    df_synth = pd.read_csv(test_synth_results_file)
    df_synth["experiment"] = df_synth["model_name"]+"_"+df_synth["temperature"].astype(str) + "_"+df_synth["generation_mode"]+"_"+df_synth["examples_per_class"].astype(str)

    top_ks = set(df_synth["top_k"].values.tolist())

    new_columns = ["experiment", "dataset"]
    new_columns.extend(list(map(lambda x:f"top_{x}_acc_diff",top_ks)))
    new_columns.append("avg_accuracy")
    new_columns.extend(list(map(lambda x:f"top_{x}_acc",top_ks)))

    experiments_to_keep = [best_exp,middle_case,worst_case]
    new_df_synth = pd.DataFrame(columns=new_columns)
    big_df_synth = pd.DataFrame(columns=new_columns)

    plots_df = pd.DataFrame()

    for experiment in experiments_to_keep:
        df_keep = df_synth[df_synth["experiment"]==experiment]
        df_keep = df_keep.apply(from_dataset_to_splits,axis=1)

        df_keep = df_keep.sort_values(by=["dataset_model", "dataset_temperature", "dataset_generation_mode", "dataset_examples_per_class"])
        for dataset in df_keep["dataset"].unique():
            df_dataset = df_keep[df_keep["dataset"]==dataset]
            new_row = {"experiment":experiment,"dataset":dataset}
            #group by top_k and avg the accuracy and acc_diff
            for top_k in top_ks:
                df_top = df_dataset[df_dataset["top_k"]==top_k]
                new_row[f"top_{top_k}_acc_diff"] = df_top["accuracy_diff"].mean()
                new_row[f"top_{top_k}_acc"] = df_top["accuracy"].mean()
                new_row["avg_accuracy"] = df[df["experiment"]==experiment]["accuracy"].mean()
            big_df_synth = pd.concat([big_df_synth,pd.DataFrame(new_row,index=[0])])

    def get_avg_acc_diff(row, top_ks):
        cumulative_acc_diff = 0
        for top_k in top_ks:
            cumulative_acc_diff += row[f"top_{top_k}_acc_diff"]
        row["avg_acc_diff"] = cumulative_acc_diff/len(top_ks)
        return row

    for experiment in experiments_to_keep:
        df_keep = df_synth[df_synth["experiment"]==experiment]
        df_keep = df_keep.apply(from_dataset_to_splits,axis=1)

        df_keep = df_keep.sort_values(by=["dataset_model", "dataset_temperature", "dataset_generation_mode", "dataset_examples_per_class"])
        exp_in_dataset = big_df_synth[big_df_synth["experiment"]==experiment]
        exp_in_dataset = exp_in_dataset.apply(get_avg_acc_diff, axis=1, top_ks=top_ks)
        #select the row with the lowest avg_acc_diff
        best_dataset = exp_in_dataset[exp_in_dataset["avg_acc_diff"]==exp_in_dataset["avg_acc_diff"].min()]["dataset"].values[0]
        #select the row with the highest avg_acc_diff
        worst_dataset = exp_in_dataset[exp_in_dataset["avg_acc_diff"]==exp_in_dataset["avg_acc_diff"].max()]["dataset"].values[0]
        #get the mean of all the avg_acc_diff
        avgerage_acc_diff = exp_in_dataset["avg_acc_diff"].mean()
        #select the row with the closes avg_acc_diff to average_acc_diff
        avg_dataset = exp_in_dataset.iloc[(exp_in_dataset["avg_acc_diff"]-avgerage_acc_diff).abs().argsort()[:1]]["dataset"].values[0]
        datasets_to_keep = [best_dataset,avg_dataset,worst_dataset]
        for dataset in datasets_to_keep:
            df_dataset = df_keep[df_keep["dataset"]==dataset]
            new_row = {"experiment":experiment,"dataset":dataset}
            #group by top_k and avg the accuracy and acc_diff
            for top_k in top_ks:
                df_top = df_dataset[df_dataset["top_k"]==top_k]
                new_row[f"top_{top_k}_acc_diff"] = df_top["accuracy_diff"].mean()
                new_row[f"top_{top_k}_acc"] = df_top["accuracy"].mean()
                new_row["avg_accuracy"] = df[df["experiment"]==experiment]["accuracy"].mean()
            new_df_synth = pd.concat([new_df_synth,pd.DataFrame(new_row,index=[0])])

    new_df_synth.to_csv(rq2_file,index=False, float_format='%.3f')


    df_keep = df_synth.copy()
    df_keep = df_keep.apply(from_dataset_to_splits,axis=1)

    df_keep = df_keep.sort_values(by=["dataset_model", "dataset_temperature", "dataset_generation_mode", "dataset_examples_per_class"])
    for experiment in df_keep["experiment"].unique():
        df_keep_exp = df_keep[df_keep["experiment"]==experiment]
        for dataset in df_keep_exp["dataset"].unique():
            df_dataset = df_keep_exp[df_keep_exp["dataset"]==dataset]
            new_row = {"experiment":experiment,"dataset":dataset}
            #group by top_k and avg the accuracy and acc_diff
            for top_k in top_ks:
                df_top = df_dataset[df_dataset["top_k"]==top_k]
                new_row[f"top_{top_k}_acc_diff"] = df_top["accuracy_diff"].mean()
                new_row[f"top_{top_k}_acc_improvement"] = df_top["accuracy"].mean() - df[df["experiment"]==experiment]["accuracy"].mean()

            plots_df = pd.concat([plots_df,pd.DataFrame(new_row,index=[0])])
    plots_df.to_csv("plots_rq2.csv",index=False, float_format='%.3f')

    for top_k in top_ks:
        output_plots_folder = os.path.join(rq2_plot_folder, f"top_{top_k}")
        os.makedirs(output_plots_folder, exist_ok=True)
        ax = sns.displot(data=plots_df, x=f"top_{top_k}_acc_diff", palette = "hls", kind = "kde")
        plt.savefig(os.path.join(output_plots_folder,f"acc_diff.jpg"))
        ax = sns.displot(data=plots_df, x=f"top_{top_k}_acc_improvement", palette = "hls", kind = "kde")
        plt.savefig(os.path.join(output_plots_folder,f"acc_improvement.jpg"))
            