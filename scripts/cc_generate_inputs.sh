paper_dir=temp/paper
mkdir -p "$paper_dir"
sbatch_dir=temp/paper/sbatch
mkdir -p "$sbatch_dir"

wall_time="23:59:00"
memory="60GB"

# # Rough runs using BPOSD decoder on toric code
# for repeat in $(seq 1 6); do
#     name=unrot_bposd_xzzx_zbias_$repeat
#     rm -rf $paper_dir/$name/inputs
#     rm -rf $paper_dir/$name/logs
#     bn3d generate-input -i "$paper_dir/$name/inputs" \
#         --lattice kitaev --boundary toric --deformation xzzx --ratio equal  \
#         --sizes "9,13,17,21" --decoder BeliefPropagationOSDDecoder --bias Z \
#         --eta "30,100" --prob "0:0.5:0.02"
#     bn3d cc-sbatch --data_dir "$paper_dir/$name" --n_array 50 --memory $memory \
#         --wall_time "$wall_time" --trials 1667 --split 1 $sbatch_dir/$name.sbatch
# 
#     name=unrot_bposd_undef_zbias_$repeat
#     rm -rf $paper_dir/$name/inputs
#     rm -rf $paper_dir/$name/logs
#     bn3d generate-input -i "$paper_dir/$name/inputs" \
#         --lattice kitaev --boundary toric --deformation none --ratio equal \
#         --sizes "9,13,17,21" --decoder BeliefPropagationOSDDecoder --bias Z \
#         --eta "30,100" --prob "0:0.5:0.02"
#     bn3d cc-sbatch --data_dir "$paper_dir/$name" --n_array 50 --memory $memory \
#         --wall_time "$wall_time" --trials 1667 --split 1 $sbatch_dir/$name.sbatch
# done

# Subthreshold scaling coprime 4k+2 runs for scaling with distance.
for repeat in $(seq 1 10); do
    name=sts_coprime_scaling_etainf_$repeat
    rm -rf $paper_dir/$name/inputs
    rm -rf $paper_dir/$name/logs
    sizes="6,10,14,18"
    bn3d generate-input -i "$paper_dir/$name/inputs" \
        --code_class LayeredRotatedToricCode --noise_class DeformedXZZXErrorModel \
        --ratio coprime \
        --sizes "$sizes" --decoder BeliefPropagationOSDDecoder --bias Z \
        --eta "inf" --prob "0.45:0.49:0.01"
    bn3d cc-sbatch --data_dir "$paper_dir/$name" --n_array 6 --memory $memory \
        --wall_time "$wall_time" --trials 50000 --split 32 $sbatch_dir/$name.sbatch
done

# Threshold runs for coprime 4k+2.
name=thr_coprime_scaling_eta1000
rm -rf $paper_dir/$name/inputs
rm -rf $paper_dir/$name/logs
sizes="6,10,14,18"
bn3d generate-input -i "$paper_dir/$name/inputs" \
    --code_class LayeredRotatedToricCode --noise_class DeformedXZZXErrorModel \
    --ratio coprime \
    --sizes "$sizes" --decoder BeliefPropagationOSDDecoder --bias Z \
    --eta "1000" --prob "0.20:0.55:0.05"
bn3d cc-sbatch --data_dir "$paper_dir/$name" --n_array 39 --memory $memory \
    --wall_time "$wall_time" --trials 10000 --split 32 $sbatch_dir/$name.sbatch
