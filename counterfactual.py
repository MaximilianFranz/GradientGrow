from nelder_mead import nelder_mead
import numpy as np
from scipy.optimize import minimize
from statsmodels import robust
import gradientgrow as gg

from utils import construct_test_data_around_instance


class CounterFactualFinder():
    def __init__(self, clf, data, chosen_attributes=None):
        self.clf = clf
        self.data = data
        self.chosen_attributes = chosen_attributes

    def minimize(self, instance, target_value=1, step=0):
        def func(x):
            """
            Returns the function to optimize
            X must be np.array
            """

            value = (2*target_value - self.clf.predict_proba(x.reshape(1, -1))[0, 1])**3
            return value

        return minimize(func, instance, method="Nelder-Mead").x

    def first_counterfactual_with_nelder_mead(self, instance, target_value=1, step=10):
        """
        Args:
            instance:
            target_value:

        Returns:

        """
        def func(x):
            """
            Returns the function to optimize
            X must be np.array
            """

            value = target_value - self.clf.predict_proba(x.reshape(1, -1))[0, 1]
            return value

        return nelder_mead(func, instance, step=step)[0]

    def improved_nelder_mead(self, instance, target_value=1, weigths=None, step=10, eps=0.3):

        mad = np.array(robust.mad(self.data, axis=0))
        non_zero = mad[mad != 0] # make sure not to devide by zero

        def manhattan_distance(y, x=instance, weigths=weigths):

            if weigths is None:
                weigths = np.full(len(non_zero), 10)

            abs = np.abs(x - y)[mad != 0]

            result = np.nansum(np.divide(abs, non_zero) * weigths)
            if np.isinf(result):
                return 0
            return result

        def func(x, l=20):

            value = abs(target_value - self.clf.predict_proba(x.reshape(1, -1))[0, 1])
            optimize = value + l*manhattan_distance(x)
            # print(str(value) + " " + str(l*manhattan_distance(x)))
            return optimize

        result = minimize(func, instance, method="Nelder-Mead", options={'adaptive': True}).x
        if np.array_equal(result,instance):
            return self.random(instance, target_value=target_value)
        else:
            return result

    def random(self, instance, target_value=1):

        counterfact = None
        max_distance=0.3

        while not counterfact:
            print(max_distance)
            sample = construct_test_data_around_instance(self.data, instance, max_distance=max_distance)
            if len(sample) == 0:
                max_distance += 0.3
                continue

            pred = self.clf.predict(sample)
            sample = sample[pred == target_value]
            if len(sample) > 0:
                counterfact = sample[0]
                break
            else:
                max_distance += 0.3

        return counterfact

    def get_first_adversarial(self, original_instance, features):
        """
        Using the GradientSearch approach this method searches the first adversarial
        instance to feed into magnetic_sampling.
        """
        # GradientSearch returns only the two chosen attributes
        dec = gg.Decision(self.data,
                          features,
                          original_instance,
                          self.clf)
        # TODO: Automate Parameters
        dec.gradient_search(step=0.05, scale=1.0, nsample=100)
        return dec.get_last_instance()


