from select import select
import pandas as pd
import os
from django.conf import settings

from .models import RawFile, SpectromineQueue, SpectromineWorker, NoteFile, \
    SsdStorage, MaxquantQueue, MaxquantWorker, MsfraggerQueue, \
    MsfraggerWorker, PdQueue, PdWorker, UserProfile
from plotly.graph_objs import Scatter, Histogram
from plotly.offline import plot
import plotly.graph_objs as go
# from plotly.graph_objs.scatter import Marker


def MaxquantPlot(pk, comparison_type, run_1_pk, run_2_pk):
    run_1_pk, run_2_pk = int(run_1_pk), int(run_2_pk)
    xml_file = MaxquantQueue.objects.filter(pk=pk)[0].setting_xml
    evidence_file = MaxquantQueue.objects.filter(pk=pk)[0].evidence_file
    protein_file = MaxquantQueue.objects.filter(pk=pk)[0].protein_file
    peptide_file = MaxquantQueue.objects.filter(pk=pk)[0].peptide_file
    other_file = MaxquantQueue.objects.filter(pk=pk)[0].other_file
    imported_file = evidence_file
    filename = os.path.join(settings.MEDIA_ROOT, imported_file.name)
    imported_data = pd.read_csv(filename, sep='\t')
    imported_data['normlized'] = 0
    select_data = imported_data[[
        "Modified sequence", "Experiment", "Retention time",
        "Intensity", "normlized"]]
    select_data = select_data.loc[select_data[
        'Experiment'].isin([run_1_pk, run_2_pk])]
    if comparison_type == "identification":
        list_first_run = select_data.loc[select_data['Experiment'] == run_1_pk]
        list_2nd_run = select_data.loc[select_data['Experiment'] == run_2_pk]
        list_first_run = list_first_run.assign(common=True)
        for index, row in list_first_run.iterrows():
            if list_2nd_run[list_2nd_run['Modified sequence']
                            == row["Modified sequence"]].empty:
                list_first_run.at[index, 'common'] = False
        list_not_in_2nd_run = list_first_run.loc[list_first_run[
            'common'] == False]
        return plot({"data":
                    [Histogram(x=list_not_in_2nd_run['Retention time'],
                               name=f"Peptide in run {run_2_pk}"
                               f" not {run_1_pk}"),
                     Histogram(x=list_first_run['Retention time'],
                               name=f"All {len(list_first_run.index)} Peptides"
                               f" in {run_1_pk}",
                               visible='legendonly'),
                     Histogram(x=list_2nd_run['Retention time'],
                               name=f"All {len(list_2nd_run.index)} Peptides"
                               f" in {run_2_pk}",
                               visible='legendonly'),
                     ],

                     "layout":
                     go.Layout(width=1500,
                               title=f"There are "
                               f"{len(list_not_in_2nd_run.index)}"
                               f" Peptide in run {run_1_pk} not {run_2_pk}")},
                    output_type='div', show_link=False, link_text="",)
    elif comparison_type == "intensity":

        # Average of each modified sequence
        df_refernce = select_data.groupby(
            'Modified sequence').mean().reset_index()
        # normlized the intensity
        select_data.normlized = select_data.normlized.astype(float)
        for index, row in select_data.iterrows():
            average = df_refernce.loc[df_refernce['Modified sequence']
                                      == row['Modified sequence']]
            select_data.at[index, 'normlized'] = row['Intensity'] / \
                average['Intensity'].iloc[0]
        return plot({"data":
                     [Scatter(x=select_data[select_data[
                         "Experiment"] == run_1_pk]['Retention time'],
                         y=select_data[select_data["Experiment"] ==
                                       run_1_pk]['normlized'],
                         mode='markers',
                         name=f'{run_1_pk} intensity /average intensity',
                         visible=True,

                     ),
                         Scatter(x=select_data[select_data[
                             "Experiment"] == run_2_pk]['Retention time'],
                         y=select_data[select_data["Experiment"] ==
                                       run_2_pk]['normlized'],
                         mode='markers',
                         name=f'{run_2_pk} intensity /average intensity',
                         visible="legendonly",

                     ),

                     ],

                     "layout":
                     go.Layout(width=1500,
                               title="Intensity Comparison"
                               " (R=1 means only found in one run,"
                               "<1 means lower, >1 means higher)")},
                    output_type='div', show_link=False, link_text="",)
