from django.db import models
import pandas as pd
from algorithms.utastar import utastar

# Create your models here.
class Problem(models.Model):
    name = models.CharField(max_length=50)
    problem_file = models.FileField(upload_to="problems/")

    def run_utastar(self):
        """
        Run UTASTAR with model's data.
        """
        with open(self.problem_file.path, "rb") as f:
            problem = pd.read_excel(
                f,
                sheet_name=[0, 1],
                index_col=0,
                true_values=["True"],
                false_values=["False"],
            )
            multicrit_tbl = problem[0]
            crit_options = problem[1]

            crit_monot = crit_options.iloc[:, 0].to_dict()
            a_split = crit_options.iloc[:, 1].to_dict()

            self.result = utastar(multicrit_tbl, crit_monot, a_split, 0.05, 0.01)