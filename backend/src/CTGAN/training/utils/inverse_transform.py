import pandas as pd
import numpy as np

def inverse_transform(data, transformer, sigmas=None):
    st = 0
    recovered_column_data_list = []
    column_names = []

    for column_transform_info in transformer._column_transform_info_list:
        dim = column_transform_info.output_dimensions
        column_data = data[:, st : st + dim]
        if column_transform_info.column_type == 'continuous':
            gm = column_transform_info.transform
            transformed_df = pd.DataFrame(column_data[:, :2], columns=list(gm.get_output_sdtypes())).astype(float)
            transformed_df[transformed_df.columns[1]] = np.argmax(column_data[:, 1:], axis=1)

            if sigmas is not None:
                transformed_df.iloc[:, 0] = np.random.normal(transformed_df.iloc[:, 0], sigmas[st])

            recovered_column_data = gm.reverse_transform(transformed_df)

        else:
            ohe = column_transform_info.transform
            transformed_df = pd.DataFrame(column_data, columns=list(ohe.get_output_sdtypes()))
            recovered_column_data = ohe.reverse_transform(transformed_df)[column_transform_info.column_name]

        recovered_column_data_list.append(recovered_column_data)
        column_names.append(column_transform_info.column_name)
        st += dim 

    recovered_data = pd.DataFrame(np.column_stack(recovered_column_data_list), columns=column_names).astype(transformer._column_raw_dtypes)

    return recovered_data if transformer.dataframe else recovered_data.to_numpy()
