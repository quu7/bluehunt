from django.db import models
import pandas as pd
from algorithms.utastar import utastar

# Create your models here.
class Problem(models.Model):
    name = models.CharField(max_length=50)
    problem_file = models.FileField(upload_to="problems/")
    delta = models.FloatField(default=0.05)
    epsilon = models.FloatField(default=0.01)

    def __str__(self):
        return f"{self.name} ({self.problem_file.name}) ({self.id})"

    def run_utastar(self):
        """
        Run UTASTAR with model's data.
        """
        multicrit_tbl, crit_options = self.get_dataframe()

        crit_monot = crit_options.iloc[:, 0].to_dict()
        a_split = crit_options.iloc[:, 1].to_dict()

        return utastar(multicrit_tbl, crit_monot, a_split, self.delta, self.epsilon)

    def get_dataframe(self):
        with open(self.problem_file.path, "rb") as f:
            problem = pd.read_excel(
                f,
                sheet_name=[0, 1],
                index_col=0,
                true_values=["True", "TRUE", "true"],
                false_values=["False", "FALSE", "false"],
            )
            multicrit_tbl = problem[0]
            crit_options = problem[1]

            return (multicrit_tbl, crit_options)
