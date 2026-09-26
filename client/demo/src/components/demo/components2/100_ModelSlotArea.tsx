import React, { useEffect, useMemo, useState } from "react";
import { useAppState } from "../../../001_provider/001_AppStateProvider";
import { useGuiState } from "../001_GuiStateProvider";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

export type ModelSlotAreaProps = {};

const SortTypes = {
    slot: "slot",
    name: "name",
} as const;
export type SortTypes = (typeof SortTypes)[keyof typeof SortTypes];

export const ModelSlotArea = (_props: ModelSlotAreaProps) => {
    const { serverSetting, getInfo, webEdition } = useAppState();
    const guiState = useGuiState();
    const [sortType, setSortType] = useState<SortTypes>("slot");
    const [page, setPage] = useState(0);
    const pageSize = 8;
    const modelSlots = serverSetting.serverSetting.modelSlots || [];

    const filledSlots = useMemo(() => {
        const slots = modelSlots.filter((slot) => !!slot.modelFile);
        return sortType == "slot" ? slots : slots.slice().sort((a, b) => a.name.localeCompare(b.name));
    }, [modelSlots, sortType]);
    const pageCount = Math.max(1, Math.ceil(filledSlots.length / pageSize));
    const visiblePage = Math.min(page, pageCount - 1);
    const selectedPosition = filledSlots.findIndex((slot) => slot.slotIndex == serverSetting.serverSetting.modelSlotIndex);

    useEffect(() => {
        if (selectedPosition >= 0) setPage(Math.floor(selectedPosition / pageSize));
    }, [selectedPosition]);

    const modelTiles = filledSlots.slice(visiblePage * pageSize, (visiblePage + 1) * pageSize).map((x) => {
        const tileContainerClass = x.slotIndex == serverSetting.serverSetting.modelSlotIndex ? "model-slot-tile-container-selected" : "model-slot-tile-container";
        const name = x.name;

        const modelDir = x.slotIndex == "Beatrice-JVS" ? "model_dir_static" : serverSetting.serverSetting.voiceChangerParams.model_dir;
        const icon = x.iconFile.length > 0 ? modelDir + "/" + x.slotIndex + "/" + x.iconFile.split(/[\/\\]/).pop() : "./assets/icons/human.png";

        const iconElem =
            x.iconFile.length > 0 ? (
                <>
                    {/* <img className="model-slot-tile-icon" src={serverSetting.serverSetting.voiceChangerParams.model_dir + "/" + x.slotIndex + "/" + x.iconFile.split(/[\/\\]/).pop()} alt={x.name} /> */}
                    <img className="model-slot-tile-icon" src={icon} alt={x.name} />
                    <div className="model-slot-tile-vctype">{x.voiceChangerType}</div>
                </>
            ) : (
                <>
                    <div className="model-slot-tile-icon-no-entry">no image</div>
                    <div className="model-slot-tile-vctype">{x.voiceChangerType}</div>
                </>
            );

        const clickAction = async () => {
            // @ts-ignore
            const dummyModelSlotIndex = Math.floor(Date.now() / 1000) * 1000 + x.slotIndex;
            await serverSetting.updateServerSettings({ ...serverSetting.serverSetting, modelSlotIndex: dummyModelSlotIndex });
            setTimeout(() => {
                // quick hack
                getInfo();
            }, 1000 * 2);
        };

        return (
            <button type="button" key={x.slotIndex} className={tileContainerClass} onClick={clickAction} aria-label={`${x.slotIndex}. ${x.name}`}>
                <div className="model-slot-tile-icon-div">{iconElem}</div>
                <div className="model-slot-tile-dscription">
                    {x.slotIndex}. {name}
                </div>
            </button>
        );
    });

    const onModelSlotEditClicked = () => {
        guiState.setModelSlotDialogRequest({ screen: "Main", targetIndex: 0 });
        guiState.stateControls.showModelSlotManagerCheckbox.updateState(true);
    };
    const onModelSlotUploadClicked = () => {
        const targetSlot = modelSlots.find((slot) => !slot.modelFile && typeof slot.slotIndex === "number");
        if (!targetSlot || typeof targetSlot.slotIndex !== "number") {
            onModelSlotEditClicked();
            return;
        }
        guiState.setModelSlotDialogRequest({ screen: "FileUploader", targetIndex: targetSlot.slotIndex });
        guiState.stateControls.showModelSlotManagerCheckbox.updateState(true);
    };
    const sortSlotByIdClass = sortType == "slot" ? "model-slot-sort-button-active" : "model-slot-sort-button";
    const sortSlotByNameClass = sortType == "name" ? "model-slot-sort-button-active" : "model-slot-sort-button";
    const modelSlotArea = (
        <div className="model-slot-area">
            <div className="vc-model-list-header">
                <h2>模型列表</h2>
                <span>
                    {filledSlots.length} / {modelSlots.length} 使用中的插槽
                </span>
            </div>
            <div className="model-slot-panel">
                <div className="model-slot-tiles-container">{modelTiles}</div>
                <div className="model-slot-buttons">
                    <div className="model-slot-sort-buttons">
                        <button
                            type="button"
                            aria-label="按插槽排序"
                            className={sortSlotByIdClass}
                            onClick={() => {
                                setSortType("slot");
                            }}
                        >
                            <FontAwesomeIcon icon={["fas", "arrow-down-1-9"]} style={{ fontSize: "1rem" }} />
                        </button>
                        <button
                            type="button"
                            aria-label="按名称排序"
                            className={sortSlotByNameClass}
                            onClick={() => {
                                setSortType("name");
                            }}
                        >
                            <FontAwesomeIcon icon={["fas", "arrow-down-a-z"]} style={{ fontSize: "1rem" }} />
                        </button>
                    </div>
                    <button type="button" className="model-slot-button" onClick={onModelSlotUploadClicked}>
                        上传
                    </button>
                    <button type="button" className="model-slot-button" onClick={onModelSlotEditClicked}>
                        编辑
                    </button>
                </div>
            </div>
            <div className="vc-model-pages" aria-label="模型列表分页">
                <button type="button" disabled={visiblePage == 0} onClick={() => setPage(visiblePage - 1)}>
                    ‹
                </button>
                <span>
                    {visiblePage + 1} / {pageCount}
                </span>
                <button type="button" disabled={visiblePage >= pageCount - 1} onClick={() => setPage(visiblePage + 1)}>
                    ›
                </button>
            </div>
        </div>
    );

    if (webEdition) {
        return <></>;
    }

    return modelSlotArea;
};
